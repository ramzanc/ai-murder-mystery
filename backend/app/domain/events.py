from collections.abc import Iterable
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.investigation import (
    InvestigationSession,
    QuestionEvent,
)
from app.domain.theory import FinalSubmission

class EventModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

class SessionStarted(EventModel):
    type: Literal["session_started"] = "session_started"
    case_id: str = Field(min_length=1)
    discovered_evidence_ids: tuple[str, ...] = ()


class QuestionAsked(EventModel):
    type: Literal["question_asked"] = "question_asked"
    question: QuestionEvent


class TheorySubmitted(EventModel):
    type: Literal["theory_submitted"] = "theory_submitted"
    submission: FinalSubmission


SessionEventPayload = Annotated[
    SessionStarted | QuestionAsked | TheorySubmitted,
    Field(discriminator="type"),
]

class StoredSessionEvent(EventModel):
    session_id: UUID
    sequence: int = Field(ge=1)
    idempotency_key: str = Field(
        min_length=1,
        max_length=200,
    )
    payload: SessionEventPayload


class ReplayError(ValueError):
    """Raised when an event stream cannot be replayed safely."""


def replay_session(
    events: Iterable[StoredSessionEvent],
) -> InvestigationSession:
    ordered_events = tuple(events)

    if not ordered_events:
        raise ReplayError(
            "Cannot replay an empty session event stream."
        )

    expected_session_id = ordered_events[0].session_id
    session: InvestigationSession | None = None

    for expected_sequence, stored_event in enumerate(
        ordered_events,
        start=1,
    ):
        if stored_event.session_id != expected_session_id:
            raise ReplayError(
                "An event stream cannot contain multiple "
                "session IDs."
            )

        if stored_event.sequence != expected_sequence:
            raise ReplayError(
                "Expected event sequence "
                f"{expected_sequence}, got "
                f"{stored_event.sequence}."
            )

        session = _apply_event(
            session=session,
            stored_event=stored_event,
        )

    if session is None:
        raise ReplayError(
            "Event replay did not produce a session."
        )

    return session

def _apply_event(
    *,
    session: InvestigationSession | None,
    stored_event: StoredSessionEvent,
) -> InvestigationSession:
    payload = stored_event.payload

    if isinstance(payload, SessionStarted):
        if session is not None:
            raise ReplayError(
                "A session can only be started once."
            )

        if stored_event.sequence != 1:
            raise ReplayError(
                "SessionStarted must be the first event."
            )

        return InvestigationSession(
            case_id=payload.case_id,
            discovered_evidence_ids=(
                payload.discovered_evidence_ids
            ),
        )

    if session is None:
        raise ReplayError(
            "The first event must be SessionStarted."
        )

    if isinstance(payload, QuestionAsked):
        if session.is_finalized:
            raise ReplayError(
                "A finalized session cannot accept questions."
            )

        if payload.question.sequence != session.next_sequence:
            raise ReplayError(
                "Expected question sequence "
                f"{session.next_sequence}, got "
                f"{payload.question.sequence}."
            )

        return InvestigationSession(
            case_id=session.case_id,
            events=session.events + (payload.question,),
            discovered_evidence_ids=(
                session.discovered_evidence_ids
            ),
            final_submission=session.final_submission,
        )

    if isinstance(payload, TheorySubmitted):
        if session.is_finalized:
            raise ReplayError(
                "A session can only be finalized once."
            )

        return InvestigationSession(
            case_id=session.case_id,
            events=session.events,
            discovered_evidence_ids=(
                session.discovered_evidence_ids
            ),
            final_submission=payload.submission,
        )

    raise AssertionError(
        f"Unhandled event payload: {payload!r}"
    )