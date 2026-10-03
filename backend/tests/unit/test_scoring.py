from pathlib import Path

import pytest

from app.application.case_loader import load_case
from app.application.scoring import score_theory
from app.domain.theory import Theory


BACKEND_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_CASE_PATH = BACKEND_ROOT / "cases" / "sample_case.json"


@pytest.fixture
def case():
    return load_case(SAMPLE_CASE_PATH)


def test_correct_theory_scores_100(case):
    theory = Theory(
        killer_id=case.solution.killer_id,
        motive=case.solution.motive,
        method=case.solution.method,
        evidence_ids=case.solution.key_evidence_ids,
    )

    score = score_theory(
        case=case,
        theory=theory,
    )

    assert score.killer_correct is True
    assert score.motive_correct is True
    assert score.method_correct is True

    assert score.killer_points == 40
    assert score.motive_points == 20
    assert score.method_points == 20
    assert score.evidence_points == 20

    assert score.total_points == 100
    assert score.solved is True


def test_wrong_killer_loses_killer_points(case):
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

    score = score_theory(
        case=case,
        theory=theory,
    )

    assert score.killer_correct is False
    assert score.killer_points == 0
    assert score.total_points == 60
    assert score.solved is False


def test_one_correct_evidence_scores_ten_points(case):
    canonical_id = (
        case.solution.key_evidence_ids[0]
    )

    noncanonical_id = next(
        evidence.id
        for evidence in case.initial_evidence
        if evidence.id
        not in case.solution.key_evidence_ids
    )

    theory = Theory(
        killer_id=case.solution.killer_id,
        motive=case.solution.motive,
        method=case.solution.method,
        evidence_ids=(
            canonical_id,
            noncanonical_id,
        ),
    )

    score = score_theory(
        case=case,
        theory=theory,
    )

    assert score.evidence_points == 10
    assert score.total_points == 90


def test_scoring_normalizes_case_and_whitespace(case):
    theory = Theory(
        killer_id=case.solution.killer_id,
        motive=(
            "  "
            + case.solution.motive.upper()
            + "  "
        ),
        method=(
            "  "
            + case.solution.method.upper()
            + "  "
        ),
        evidence_ids=case.solution.key_evidence_ids,
    )

    score = score_theory(
        case=case,
        theory=theory,
    )

    assert score.motive_correct is True
    assert score.method_correct is True
