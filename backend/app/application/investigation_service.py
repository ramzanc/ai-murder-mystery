from uuid import UUID, uuid4

from app.application.ports import (
    CaseFinder,
    SessionRecord,
    UnitOfWork,
)
from app.application.scoring import TheoryScore, score_theory
from app.domain.case import CaseManifest
from app.domain.evidence import Evidence
from app.domain.investigation import (
    InvestigationSession,
    QuestionEvent,
    QuestionTopic,
)
from app.domain.suspect import Suspect
from app.domain.theory import FinalSubmission, Theory


class InvestigationError(ValueError):
    """Base error for invalid investigation operations."""


class InvalidSuspectError(InvestigationError):
    """Raised when an action references a suspect outside the case."""


class InvalidQuestionTopicError(InvestigationError):
    """Raised when the requested deterministic question topic is unsupported."""


class SessionCaseMismatchError(InvestigationError):
    """Raised when a session is used with a different case."""


class InvestigationAlreadyFinalizedError(InvestigationError):
    """Raised when an investigation has already been finalized."""


class CaseNotFoundError(LookupError):
    """Raised when an investigation references an unknown case."""


class SessionNotFoundError(LookupError):
    """Raised when an investigation session cannot be found."""


def start_session(case: CaseManifest) -> InvestigationSession:
    return InvestigationSession(
        case_id=str(case.id),
        discovered_evidence_ids=tuple(
            str(evidence.id)
            for evidence in case.initial_evidence
        ),
    )


def ask_question(
    case: CaseManifest,
    session: InvestigationSession,
    suspect_id: str,
    topic: QuestionTopic | str,
) -> InvestigationSession:
    _ensure_session_matches_case(case, session)

    suspect = _find_suspect(case, suspect_id)
    question_topic = _parse_question_topic(topic)

    question = _build_question(question_topic)
    answer = _build_answer(suspect, question_topic)

    event = QuestionEvent(
        sequence=session.next_sequence,
        suspect_id=str(suspect.id),
        topic=question_topic,
        question=question,
        answer=answer,
    )

    return session.model_copy(
        update={
            "events": session.events + (event,),
        }
    )

def _ensure_session_matches_case(
    case: CaseManifest,
    session: InvestigationSession,
) -> None:
    if session.case_id != str(case.id):
        raise SessionCaseMismatchError(
            f"Session belongs to case {session.case_id!r}, "
            f"not {str(case.id)!r}."
        )


def _find_suspect(
    case: CaseManifest,
    suspect_id: str,
) -> Suspect:
    for suspect in case.suspects:
        if str(suspect.id) == suspect_id:
            return suspect

    raise InvalidSuspectError(
        f"Unknown suspect ID: {suspect_id!r}."
    )


def _parse_question_topic(
    topic: QuestionTopic | str,
) -> QuestionTopic:
    if isinstance(topic, QuestionTopic):
        return topic

    try:
        return QuestionTopic(topic)
    except ValueError as exc:
        allowed_topics = ", ".join(
            question_topic.value
            for question_topic in QuestionTopic
        )

        raise InvalidQuestionTopicError(
            f"Unsupported question topic {topic!r}. "
            f"Allowed topics: {allowed_topics}."
        ) from exc


def _build_question(topic: QuestionTopic) -> str:
    match topic:
        case QuestionTopic.ALIBI:
            return "Where were you around the time of the incident?"

        case QuestionTopic.SECRET:
            return "Is there anything important you're hiding from us?"

    raise AssertionError(
        f"Unhandled question topic: {topic!r}"
    )


def _build_answer(
    suspect: Suspect,
    topic: QuestionTopic,
) -> str:
    match topic:
        case QuestionTopic.ALIBI:
            return (
                f"{suspect.name}: My public account is unchanged. "
                f"{suspect.public_profile}"
            )

        case QuestionTopic.SECRET:
            return (
                f"{suspect.name}: I don't have anything else "
                "to add about that right now."
            )

    raise AssertionError(
        f"Unhandled question topic: {topic!r}"
    )


def submit_final_theory(
    case: CaseManifest,
    session: InvestigationSession,
    theory: Theory,
) -> tuple[InvestigationSession, TheoryScore]:
    _ensure_session_matches_case(case, session)

    if session.is_finalized:
        raise InvestigationAlreadyFinalizedError(
            "official accusation has already been submitted"
        )

    suspect_ids = {
        suspect.id
        for suspect in case.suspects
    }

    if theory.killer_id not in suspect_ids:
        raise InvalidSuspectError(
            f"unknown suspect: {theory.killer_id}"
        )

    discovered_evidence = set(
        session.discovered_evidence_ids
    )

    unavailable_evidence = (
        set(theory.evidence_ids)
        - discovered_evidence
    )

    if unavailable_evidence:
        raise InvestigationError(
            "theory references undiscovered evidence: "
            f"{sorted(unavailable_evidence)}"
        )

    score = score_theory(
        case=case,
        theory=theory,
    )

    submission = FinalSubmission(
        theory=theory,
        score=score.total_points,
    )

    updated_session = session.model_copy(
        update={
            "final_submission": submission,
        }
    )

    return updated_session, score


class InvestigationUseCases:
    def __init__(
        self,
        *,
        unit_of_work: UnitOfWork,
        find_case: CaseFinder,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._find_case = find_case

    async def create_session(
        self,
        case_id: str,
    ) -> SessionRecord:
        case = self._require_case(case_id)

        record = SessionRecord(
            id=uuid4(),
            session=start_session(case),
        )

        async with self._unit_of_work:
            await self._unit_of_work.sessions.add(record)

        return record

    async def get_session(
        self,
        session_id: UUID,
    ) -> SessionRecord:
        async with self._unit_of_work:
            return await self._require_session(session_id)

    async def get_discovered_evidence(
        self,
        session_id: UUID,
    ) -> tuple[Evidence, ...]:
        async with self._unit_of_work:
            record = await self._require_session(session_id)
            case = self._require_case(
                record.session.case_id
            )

            discovered_ids = set(
                record.session.discovered_evidence_ids
            )

            return tuple(
                evidence
                for evidence in case.initial_evidence
                if str(evidence.id) in discovered_ids
            )

    async def question_suspect(
        self,
        *,
        session_id: UUID,
        suspect_id: str,
        topic: QuestionTopic | str,
    ) -> SessionRecord:
        async with self._unit_of_work:
            record = await self._require_session(
                session_id,
                for_update=True,
            )

            case = self._require_case(
                record.session.case_id
            )

            updated_session = ask_question(
                case=case,
                session=record.session,
                suspect_id=suspect_id,
                topic=topic,
            )

            updated_record = SessionRecord(
                id=record.id,
                session=updated_session,
            )

            await self._unit_of_work.sessions.replace(
                updated_record
            )

            return updated_record

    async def submit_theory(
        self,
        *,
        session_id: UUID,
        theory: Theory,
    ) -> tuple[SessionRecord, TheoryScore]:
        async with self._unit_of_work:
            record = await self._require_session(
                session_id,
                for_update=True,
            )

            case = self._require_case(
                record.session.case_id
            )

            updated_session, score = submit_final_theory(
                case=case,
                session=record.session,
                theory=theory,
            )

            updated_record = SessionRecord(
                id=record.id,
                session=updated_session,
            )

            await self._unit_of_work.sessions.replace(
                updated_record
            )

            return updated_record, score

    def _require_case(
        self,
        case_id: str,
    ) -> CaseManifest:
        case = self._find_case(case_id)

        if case is None:
            raise CaseNotFoundError(
                f"Case {case_id!r} was not found."
            )

        return case

    async def _require_session(
        self,
        session_id: UUID,
        *,
        for_update: bool = False,
    ) -> SessionRecord:
        record = await self._unit_of_work.sessions.get(
            session_id,
            for_update=for_update,
        )

        if record is None:
            raise SessionNotFoundError(
                f"Session {str(session_id)!r} was not found."
            )

        return record
