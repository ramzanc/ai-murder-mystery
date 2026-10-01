from app.domain.case import CaseManifest
from app.domain.investigation import (
    InvestigationSession,
    QuestionEvent,
    QuestionTopic,
)
from app.domain.suspect import Suspect

class InvestigationError(ValueError):
    """Base error for invalid investigation operations."""


class InvalidSuspectError(InvestigationError):
    """Raised when an action references a suspect outside the case."""


class InvalidQuestionTopicError(InvestigationError):
    """Raised when the requested deterministic question topic is unsupported."""


class SessionCaseMismatchError(InvestigationError):
    """Raised when a session is used with a different case."""


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
