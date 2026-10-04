from typing import Annotated, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field

from app.domain.investigation import QuestionTopic


class StartingUnlockRule(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    kind: Literal["starting"] = "starting"


class QuestionUnlockRule(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    kind: Literal["question"] = "question"
    suspect_id: str = Field(
        pattern=r"^suspect_[a-z0-9_]+$",
    )
    intent: QuestionTopic


class EvidenceUnlockRule(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    kind: Literal["evidence"] = "evidence"
    evidence_id: str = Field(
        pattern=r"^evidence_[a-z0-9_]+$",
    )


UnlockRule: TypeAlias = Annotated[
    StartingUnlockRule
    | QuestionUnlockRule
    | EvidenceUnlockRule,
    Field(discriminator="kind"),
]