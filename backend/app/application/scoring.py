from pydantic import BaseModel, ConfigDict

from app.domain.case import CaseManifest
from app.domain.theory import Theory

class TheoryScore(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    killer_correct: bool
    motive_correct: bool
    method_correct: bool
    matching_evidence_ids: tuple[str, ...]

    killer_points: int
    motive_points: int
    method_points: int
    evidence_points: int
    total_points: int

    @property
    def solved(self) -> bool:
        return (
            self.killer_correct
            and self.motive_correct
            and self.method_correct
        )

def _normalize_text(value: str) -> str:
    return " ".join(
        value.casefold().split()
    )

def score_theory(
    case: CaseManifest,
    theory: Theory,
) -> TheoryScore:
    solution = case.solution

    killer_correct = (
        theory.killer_id
        == solution.killer_id
    )

    motive_correct = (
        _normalize_text(theory.motive)
        == _normalize_text(solution.motive)
    )

    method_correct = (
        _normalize_text(theory.method)
        == _normalize_text(solution.method)
    )

    canonical_evidence = set(
        solution.key_evidence_ids
    )

    matching_evidence_ids = tuple(
        evidence_id
        for evidence_id in theory.evidence_ids
        if evidence_id in canonical_evidence
    )

    killer_points = (
        40 if killer_correct else 0
    )

    motive_points = (
        20 if motive_correct else 0
    )

    method_points = (
        20 if method_correct else 0
    )

    evidence_points = min(
        len(matching_evidence_ids) * 10,
        20,
    )

    total_points = (
        killer_points
        + motive_points
        + method_points
        + evidence_points
    )

    return TheoryScore(
        killer_correct=killer_correct,
        motive_correct=motive_correct,
        method_correct=method_correct,
        matching_evidence_ids=matching_evidence_ids,
        killer_points=killer_points,
        motive_points=motive_points,
        method_points=method_points,
        evidence_points=evidence_points,
        total_points=total_points,
    )