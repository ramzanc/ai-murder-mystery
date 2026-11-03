from collections.abc import Iterable

from pydantic import BaseModel, ConfigDict, Field

from app.domain.case import CaseManifest
from app.domain.investigation import InvestigationSession

class SuspectContextError(ValueError):
    """Base error raised while constructing suspect context."""


class ContextSuspectNotFoundError(SuspectContextError):
    """Raised when the requested suspect is not in the case."""


class ContextSessionMismatchError(SuspectContextError):
    """Raised when the session belongs to another case."""


class EvidenceNotAvailableError(SuspectContextError):
    """Raised when evidence was not discovered or does not exist."""


class ContextObservation(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    description: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)

class ContextBelief(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    statement: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)

class ContextInterviewTurn(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    sequence: int = Field(ge=1)
    question: str = Field(min_length=1)
    answer: str = Field(min_length=1)

class ContextEvidence(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    kind: str = Field(min_length=1)


class SuspectContext(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    case_id: str = Field(min_length=1)
    suspect_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    occupation: str = Field(min_length=1)
    relationship_to_victim: str = Field(min_length=1)
    public_profile: str = Field(min_length=1)

    known_facts: tuple[str, ...] = ()
    observations: tuple[ContextObservation, ...] = ()
    beliefs: tuple[ContextBelief, ...] = ()
    own_chat: tuple[ContextInterviewTurn, ...] = ()
    presented_evidence: tuple[ContextEvidence, ...] = ()


def build_suspect_context(
    *,
    case: CaseManifest,
    session: InvestigationSession,
    suspect_id: str,
    presented_evidence_ids: Iterable[str] = (),
) -> SuspectContext:
    if session.case_id != str(case.id):
        raise ContextSessionMismatchError(
            f"Session belongs to case {session.case_id!r}, "
            f"not {str(case.id)!r}."
        )

    suspect = next(
        (
            candidate
            for candidate in case.suspects
            if str(candidate.id) == suspect_id
        ),
        None,
    )

    if suspect is None:
        raise ContextSuspectNotFoundError(
            f"Unknown suspect ID: {suspect_id!r}."
        )

    requested_evidence_ids = set(presented_evidence_ids)
    discovered_evidence_ids = set(
        session.discovered_evidence_ids
    )
    case_evidence_ids = {
        str(evidence.id)
        for evidence in case.initial_evidence
    }

    unknown_evidence_ids = (
        requested_evidence_ids - case_evidence_ids
    )
    if unknown_evidence_ids:
        raise EvidenceNotAvailableError(
            "Unknown evidence IDs: "
            f"{sorted(unknown_evidence_ids)}."
        )
    
    undiscovered_evidence_ids = (
        requested_evidence_ids - discovered_evidence_ids
    )

    if undiscovered_evidence_ids:
        raise EvidenceNotAvailableError(
            "Evidence has not been discovered: "
            f"{sorted(undiscovered_evidence_ids)}."
        )

    timeline_events_by_id = {
        str(event.id): event
        for event in case.timeline.events
    }

    known_facts = tuple(
        timeline_events_by_id[str(event_id)].description
        for event_id in suspect.knowledge.known_event_ids
    )

    observations = tuple(
        ContextObservation(
            description=observation.perceived_description,
            confidence=observation.confidence,
        )
        for observation in suspect.knowledge.observations
    )

    beliefs = tuple(
        ContextBelief(
            statement=belief.statement,
            confidence=belief.confidence,
        )
        for belief in suspect.knowledge.beliefs
    )

    own_chat = tuple(
        ContextInterviewTurn(
            sequence=event.sequence,
            question=event.question,
            answer=event.answer,
        )
        for event in session.events
        if event.suspect_id == suspect_id
    )

    presented_evidence = tuple(
        ContextEvidence(
            id=str(evidence.id),
            title=evidence.title,
            description=evidence.description,
            kind=evidence.kind.value,
        )
        for evidence in case.initial_evidence
        if str(evidence.id) in requested_evidence_ids
    )

    return SuspectContext(
        case_id=str(case.id),
        suspect_id=str(suspect.id),
        name=suspect.name,
        occupation=suspect.occupation,
        relationship_to_victim=(
            suspect.relationship_to_victim
        ),
        public_profile=suspect.public_profile,
        known_facts=known_facts,
        observations=observations,
        beliefs=beliefs,
        own_chat=own_chat,
        presented_evidence=presented_evidence,
    )