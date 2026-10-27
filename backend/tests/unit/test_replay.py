from pathlib import Path
from uuid import uuid4

import pytest

from app.application.case_loader import load_case
from app.application.investigation_service import (
    ask_question,
    start_session,
    submit_final_theory,
)
from app.domain.events import (
    QuestionAsked,
    ReplayError,
    SessionStarted,
    StoredSessionEvent,
    TheorySubmitted,
    replay_session,
)
from app.domain.investigation import QuestionTopic
from app.domain.theory import Theory


BACKEND_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_CASE_PATH = (
    BACKEND_ROOT
    / "cases"
    / "sample_case.json"
)


def build_complete_event_stream():
    case = load_case(SAMPLE_CASE_PATH)
    session_id = uuid4()

    initial_session = start_session(case)

    after_question = ask_question(
        case=case,
        session=initial_session,
        suspect_id=str(case.suspects[0].id),
        topic=QuestionTopic.ALIBI,
    )

    theory = Theory(
        killer_id=case.solution.killer_id,
        motive=case.solution.motive,
        method=case.solution.method,
        evidence_ids=case.solution.key_evidence_ids,
    )

    finalized_session, _ = submit_final_theory(
        case=case,
        session=after_question,
        theory=theory,
    )

    assert finalized_session.final_submission is not None

    events = (
        StoredSessionEvent(
            session_id=session_id,
            sequence=1,
            idempotency_key="start-session",
            payload=SessionStarted(
                case_id=initial_session.case_id,
                discovered_evidence_ids=(
                    initial_session.discovered_evidence_ids
                ),
            ),
        ),
        StoredSessionEvent(
            session_id=session_id,
            sequence=2,
            idempotency_key="ask-alibi",
            payload=QuestionAsked(
                question=after_question.events[-1],
            ),
        ),
        StoredSessionEvent(
            session_id=session_id,
            sequence=3,
            idempotency_key="submit-theory",
            payload=TheorySubmitted(
                submission=(
                    finalized_session.final_submission
                ),
            ),
        ),
    )

    return events, finalized_session


def test_replay_reproduces_session_snapshot() -> None:
    events, expected_session = (
        build_complete_event_stream()
    )

    rebuilt_session = replay_session(events)

    assert rebuilt_session == expected_session
    assert rebuilt_session.discovered_evidence_ids == (
        expected_session.discovered_evidence_ids
    )
    assert rebuilt_session.events == (
        expected_session.events
    )
    assert rebuilt_session.final_submission == (
        expected_session.final_submission
    )


def test_replay_rejects_sequence_gap() -> None:
    events, _ = build_complete_event_stream()

    broken_event = events[1].model_copy(
        update={
            "sequence": 3,
        }
    )

    with pytest.raises(
        ReplayError,
        match="Expected event sequence 2",
    ):
        replay_session(
            (
                events[0],
                broken_event,
            )
        )


def test_replay_rejects_mixed_session_ids() -> None:
    events, _ = build_complete_event_stream()

    foreign_event = events[1].model_copy(
        update={
            "session_id": uuid4(),
        }
    )

    with pytest.raises(
        ReplayError,
        match="multiple session IDs",
    ):
        replay_session(
            (
                events[0],
                foreign_event,
            )
        )


def test_replay_rejects_question_after_finalization() -> None:
    events, _ = build_complete_event_stream()

    late_question = StoredSessionEvent(
        session_id=events[0].session_id,
        sequence=4,
        idempotency_key="late-question",
        payload=events[1].payload,
    )

    with pytest.raises(
        ReplayError,
        match="finalized session",
    ):
        replay_session(events + (late_question,))


def test_replay_rejects_empty_stream() -> None:
    with pytest.raises(
        ReplayError,
        match="empty",
    ):
        replay_session(())