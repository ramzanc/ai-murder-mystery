from pathlib import Path

import pytest

from app.application.case_loader import load_case
from app.application.investigation_service import (
    InvestigationAlreadyFinalizedError,
    ask_question,
    start_session,
    submit_final_theory,
)
from app.application.reveal import RevealUnavailableError, build_reveal
from app.domain.investigation import QuestionTopic
from app.domain.theory import Theory
from app.presentation.terminal import run_case_browser


BACKEND_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_CASE_PATH = BACKEND_ROOT / "cases" / "sample_case.json"


def test_complete_deterministic_game_flow():
    case = load_case(SAMPLE_CASE_PATH)

    original_case_dump = (
        case.model_dump()
    )

    session = start_session(case)

    session = ask_question(
        case=case,
        session=session,
        suspect_id=case.suspects[0].id,
        topic=QuestionTopic.ALIBI,
    )

    session = ask_question(
        case=case,
        session=session,
        suspect_id=case.suspects[1].id,
        topic=QuestionTopic.SECRET,
    )

    theory = Theory(
        killer_id=case.solution.killer_id,
        motive=case.solution.motive,
        method=case.solution.method,
        evidence_ids=case.solution.key_evidence_ids,
    )

    session, score = submit_final_theory(
        case=case,
        session=session,
        theory=theory,
    )

    reveal = build_reveal(case, session)

    assert len(session.events) == 2

    assert session.is_finalized is True
    assert session.official_score == 100

    assert score.total_points == 100
    assert score.solved is True

    assert (
        reveal.killer_id
        == case.solution.killer_id
    )

    assert (
        reveal.motive
        == case.solution.motive
    )

    assert (
        reveal.method
        == case.solution.method
    )

    assert (
        case.model_dump()
        == original_case_dump
    )


def test_wrong_accusation_still_locks_scoring():
    case = load_case(SAMPLE_CASE_PATH)

    session = start_session(case)

    wrong_suspect = next(
        suspect
        for suspect in case.suspects
        if suspect.id
        != case.solution.killer_id
    )

    theory = Theory(
        killer_id=wrong_suspect.id,
        motive=case.solution.motive,
        method=case.solution.method,
        evidence_ids=case.solution.key_evidence_ids,
    )

    session, score = submit_final_theory(
        case=case,
        session=session,
        theory=theory,
    )

    assert score.solved is False
    assert session.is_finalized is True

    reveal = build_reveal(case, session)

    assert reveal.killer_id == case.solution.killer_id
    assert reveal.killer_id != wrong_suspect.id

    with pytest.raises(InvestigationAlreadyFinalizedError):
        submit_final_theory(
            case=case,
            session=session,
            theory=theory,
        )

    continued_session = ask_question(
        case=case,
        session=session,
        suspect_id=wrong_suspect.id,
        topic=QuestionTopic.ALIBI,
    )

    assert len(continued_session.events) == 1
    assert continued_session.final_submission == session.final_submission
    assert continued_session.official_score == session.official_score


def test_reveal_is_locked_before_final_submission():
    case = load_case(SAMPLE_CASE_PATH)
    session = start_session(case)

    with pytest.raises(
        RevealUnavailableError,
        match="locked until an official accusation",
    ):
        build_reveal(case, session)


def test_cli_can_play_from_dossier_to_reveal(
    monkeypatch,
    capsys,
):
    case = load_case(SAMPLE_CASE_PATH)
    answers = iter(
        (
            "1",      # view dossier
            "5",      # question a suspect
            "2",      # Marcus Reed
            "1",      # alibi
            "7",      # submit accusation
            "2",      # Marcus Reed
            "1",      # canonical motive
            "2",      # canonical method
            "1,2",    # key evidence
            "y",      # confirm the one official submission
            "0",      # exit
        )
    )

    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    run_case_browser(case)

    output = capsys.readouterr().out

    assert "--- CASE DOSSIER ---" in output
    assert "Marcus Reed: My public account is unchanged." in output
    assert "Total:    100/100" in output
    assert "=== Canonical Reveal ===" in output
    assert "Killer: Marcus Reed" in output
    assert "Investigation closed." in output
