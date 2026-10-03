from pathlib import Path

import pytest

from app.application.case_loader import load_case
from app.application.investigation_service import (
    InvalidQuestionTopicError,
    InvalidSuspectError,
    SessionCaseMismatchError,
    ask_question,
    start_session,
    InvestigationAlreadyFinalizedError,
    submit_final_theory,
)
from app.domain.investigation import QuestionTopic
from app.domain.theory import Theory


BACKEND_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_CASE_PATH = (
    BACKEND_ROOT
    / "cases"
    / "sample_case.json"
)


@pytest.fixture
def case():
    return load_case(SAMPLE_CASE_PATH)


def test_start_session_does_not_modify_case(case):
    case_before = case.model_dump()

    session = start_session(case)

    assert case.model_dump() == case_before
    assert session.case_id == str(case.id)
    assert session.events == ()


def test_start_session_owns_discovered_evidence_ids(case):
    session = start_session(case)

    expected_ids = tuple(
        str(evidence.id)
        for evidence in case.initial_evidence
    )

    assert session.discovered_evidence_ids == expected_ids

    assert session.discovered_evidence_ids is not case.initial_evidence


def test_question_appends_event_without_mutating_previous_session(
    case,
):
    session_before = start_session(case)

    suspect = case.suspects[0]

    session_after = ask_question(
        case=case,
        session=session_before,
        suspect_id=str(suspect.id),
        topic=QuestionTopic.ALIBI,
    )

    assert session_before.events == ()
    assert len(session_after.events) == 1

    event = session_after.events[0]

    assert event.sequence == 1
    assert event.suspect_id == str(suspect.id)
    assert event.topic is QuestionTopic.ALIBI
    assert event.question
    assert event.answer


def test_multiple_questions_receive_monotonic_sequence_numbers(
    case,
):
    session = start_session(case)

    first_suspect = case.suspects[0]
    second_suspect = case.suspects[1]

    session = ask_question(
        case=case,
        session=session,
        suspect_id=str(first_suspect.id),
        topic=QuestionTopic.ALIBI,
    )

    session = ask_question(
        case=case,
        session=session,
        suspect_id=str(second_suspect.id),
        topic=QuestionTopic.SECRET,
    )

    assert len(session.events) == 2

    assert [
        event.sequence
        for event in session.events
    ] == [1, 2]


def test_question_does_not_modify_case(case):
    case_before = case.model_dump()

    session = start_session(case)

    session = ask_question(
        case=case,
        session=session,
        suspect_id=str(case.suspects[0].id),
        topic=QuestionTopic.SECRET,
    )

    assert len(session.events) == 1
    assert case.model_dump() == case_before


def test_invalid_suspect_id_is_rejected(case):
    session = start_session(case)

    with pytest.raises(
        InvalidSuspectError,
        match="Unknown suspect ID",
    ):
        ask_question(
            case=case,
            session=session,
            suspect_id="suspect:not-real",
            topic=QuestionTopic.ALIBI,
        )


def test_invalid_question_topic_is_rejected(case):
    session = start_session(case)

    with pytest.raises(
        InvalidQuestionTopicError,
        match="Unsupported question topic",
    ):
        ask_question(
            case=case,
            session=session,
            suspect_id=str(case.suspects[0].id),
            topic="tell_me_the_killer",
        )


def test_session_cannot_be_used_with_another_case(case):
    session = start_session(case)

    another_case = case.model_copy(
        update={
            "id": "case:another-case",
        }
    )

    with pytest.raises(
        SessionCaseMismatchError,
        match="Session belongs to case",
    ):
        ask_question(
            case=another_case,
            session=session,
            suspect_id=str(
                another_case.suspects[0].id
            ),
            topic=QuestionTopic.ALIBI,
        )

def test_final_submission_locks_official_scoring(
    case,
):
    session = start_session(case)

    theory = Theory(
        killer_id=case.solution.killer_id,
        motive=case.solution.motive,
        method=case.solution.method,
        evidence_ids=case.solution.key_evidence_ids,
    )

    finalized_session, score = (
        submit_final_theory(
            case=case,
            session=session,
            theory=theory,
        )
    )

    assert finalized_session.is_finalized
    assert (
        finalized_session.final_submission
        is not None
    )
    assert (
        finalized_session.official_score
        == score.total_points
    )

    with pytest.raises(
        InvestigationAlreadyFinalizedError
    ):
        submit_final_theory(
            case=case,
            session=finalized_session,
            theory=theory,
        )

def test_final_submission_does_not_mutate_original_session(
    case,
):
    session = start_session(case)

    theory = Theory(
        killer_id=case.solution.killer_id,
        motive=case.solution.motive,
        method=case.solution.method,
        evidence_ids=case.solution.key_evidence_ids,
    )

    finalized_session, _ = (
        submit_final_theory(
            case=case,
            session=session,
            theory=theory,
        )
    )

    assert session.is_finalized is False
    assert session.final_submission is None
    assert session.official_score is None

    assert finalized_session is not session
    assert finalized_session.is_finalized is True