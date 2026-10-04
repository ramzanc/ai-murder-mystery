from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from app.domain.unlock import UnlockRule


class EvidenceKind(str, Enum):
    PHYSICAL = "physical"
    DOCUMENT = "document"
    DIGITAL = "digital"
    TESTIMONY = "testimony"


class Evidence(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    id: str = Field(
        pattern=r"^evidence_[a-z0-9_]+$",
    )
    title: str = Field(
        min_length=1,
        max_length=120,
    )
    description: str = Field(
        min_length=1,
        max_length=1000,
    )
    kind: EvidenceKind

    source_event_id: str | None = Field(
        default=None,
        pattern=r"^timeline_event_[a-z0-9_]+$",
    )

    unlock_rules: tuple[UnlockRule, ...] = ()