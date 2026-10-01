from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class QuestionTopic(StrEnum):
    ALIBI = "alibi"
    SECRET = "secret"

class QuestionEvent(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    sequence: int = Field(ge=1)
    suspect_id: str = Field(min_length=1)
    topic: QuestionTopic
    question: str = Field(min_length=1)
    answer: str = Field(min_length=1)


class InvestigationSession(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    case_id: str = Field(min_length=1)
    events: tuple[QuestionEvent, ...] = ()
    discovered_evidence_ids: tuple[str, ...] = ()

    @property
    def next_sequence(self) -> int:
        return len(self.events) + 1