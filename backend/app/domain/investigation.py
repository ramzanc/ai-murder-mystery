from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.domain.theory import FinalSubmission


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
    final_submission: FinalSubmission | None = None

    @property
    def next_sequence(self) -> int:
        return len(self.events) + 1

    @property
    def is_finalized(self) -> bool:
        return self.final_submission is not None

    @property
    def official_score(self) -> int | None:
        if self.final_submission is None:
            return None

        return self.final_submission.score
