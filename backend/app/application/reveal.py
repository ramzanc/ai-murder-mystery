from pydantic import BaseModel, ConfigDict

from app.domain.case import CaseManifest
from app.domain.investigation import InvestigationSession


class RevealUnavailableError(ValueError):
    """Raised when canonical truth is requested before finalization."""


class EvidenceReveal(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    id: str
    title: str
    description: str


class CaseReveal(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    killer_id: str
    killer_name: str
    motive: str
    method: str
    key_evidence: tuple[EvidenceReveal, ...]
    explanation: str


def build_reveal(
    case: CaseManifest,
    session: InvestigationSession,
) -> CaseReveal:
    if session.case_id != str(case.id):
        raise RevealUnavailableError(
            "session does not belong to this case"
        )

    if not session.is_finalized:
        raise RevealUnavailableError(
            "canonical reveal is locked until an official accusation "
            "is submitted"
        )

    solution = case.solution

    killer = next(
        suspect
        for suspect in case.suspects
        if suspect.id == solution.killer_id
    )

    evidence_by_id = {
        evidence.id: evidence
        for evidence in case.initial_evidence
    }

    key_evidence = tuple(
        EvidenceReveal(
            id=evidence_id,
            title=evidence_by_id[evidence_id].title,
            description=evidence_by_id[evidence_id].description,
        )
        for evidence_id
        in solution.key_evidence_ids
    )

    return CaseReveal(
        killer_id=killer.id,
        killer_name=killer.name,
        motive=solution.motive,
        method=solution.method,
        key_evidence=key_evidence,
        explanation=solution.explanation,
    )
