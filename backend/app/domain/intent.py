from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

class SemanticIntent(StrEnum):
    ASK_ALIBI = "ask_alibi"
    PROBE_SECRET = "probe_secret"
    ASK_TIMELINE = "ask_timeline"
    DISCUSS_EVIDENCE = "discuss_evidence"
    UNKNOWN = "unknown"


class IntentEntities(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    suspect_mentions: tuple[str, ...] = ()
    time_references: tuple[str, ...] = ()
    evidence_mentions: tuple[str, ...] = ()


class IntentProposal(BaseModel):
    """Non-authoritative structured output proposed by the LLM."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    intent: SemanticIntent
    confidence: float = Field(ge=0.0, le=1.0)
    entities: IntentEntities = Field(
        default_factory=IntentEntities,
    )

class ClassifiedIntent(BaseModel):
    """Safe application result after deterministic fallback rules."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    intent: SemanticIntent
    confidence: float = Field(ge=0.0, le=1.0)
    entities: IntentEntities = Field(
        default_factory=IntentEntities,
    )
    used_fallback: bool = False