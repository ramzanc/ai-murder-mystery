from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ClueRelevance(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class ClueAssessmentProposal(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    summary: str = Field(
        description=(
            "A concise summary of the supplied clue."
        ),
    )

    proposed_relevance: ClueRelevance = Field(
        description=(
            "The model's non-authoritative estimate "
            "of the clue's investigative relevance."
        ),
    )

    rationale: str = Field(
        description=(
            "A short explanation for the proposed relevance."
        ),
    )