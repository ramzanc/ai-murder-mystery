import re

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Theory(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    killer_id: str = Field(
        min_length=1,
        pattern=r"^suspect_[a-z0-9_]+$",
    )

    motive: str = Field(
        min_length=1,
        max_length=300,
    )

    method: str = Field(
        min_length=1,
        max_length=300,
    )

    evidence_ids: tuple[str, ...] = Field(
        min_length=2,
        max_length=3,
    )

    @field_validator("motive", "method")
    @classmethod
    def strip_text(cls, value: str) -> str:
        stripped = value.strip()

        if not stripped:
            raise ValueError("text must not be blank")

        return stripped

    @field_validator("evidence_ids")
    @classmethod
    def validate_evidence_ids(
        cls,
        evidence_ids: tuple[str, ...],
    ) -> tuple[str, ...]:
        if len(set(evidence_ids)) != len(evidence_ids):
            raise ValueError("evidence IDs must be unique")

        for evidence_id in evidence_ids:
            if re.fullmatch(r"evidence_[a-z0-9_]+", evidence_id) is None:
                raise ValueError(
                    f"invalid evidence ID: {evidence_id}"
                )

        return evidence_ids


class FinalSubmission(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    theory: Theory
    score: int = Field(ge=0, le=100)
