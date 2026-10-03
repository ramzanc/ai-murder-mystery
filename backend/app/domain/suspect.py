from pydantic import BaseModel, ConfigDict, Field

from app.domain.knowledge import SuspectKnowledge


class Suspect(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    id: str = Field(
        pattern=r"^suspect_[a-z0-9_]+$",
    )
    name: str = Field(
        min_length=1,
        max_length=100,
    )
    age: int = Field(
        ge=18,
        le=120,
    )
    occupation: str = Field(
        min_length=1,
        max_length=120,
    )
    relationship_to_victim: str = Field(
        min_length=1,
        max_length=200,
    )
    public_profile: str = Field(
        min_length=1,
        max_length=1000,
    )
    knowledge: SuspectKnowledge = Field(
        default_factory=SuspectKnowledge,
    )