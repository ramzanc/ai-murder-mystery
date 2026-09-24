from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.evidence import Evidence
from app.domain.suspect import Suspect


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Victim(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    id: str = Field(
        pattern=r"^victim_[a-z0-9_]+$",
    )
    name: str = Field(
        min_length=1,
        max_length=100,
    )
    age: int = Field(
        ge=0,
        le=120,
    )
    public_profile: str = Field(
        min_length=1,
        max_length=1000,
    )


class PublicDossier(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    summary: str = Field(
        min_length=1,
        max_length=2000,
    )
    location: str = Field(
        min_length=1,
        max_length=200,
    )
    incident_time: str = Field(
        min_length=1,
        max_length=100,
    )


class CaseManifest(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    schema_version: int = Field(
        default=1,
        ge=1,
    )
    id: str = Field(
        pattern=r"^case_[a-z0-9_]+$",
    )
    title: str = Field(
        min_length=1,
        max_length=200,
    )
    difficulty: Difficulty

    dossier: PublicDossier
    victim: Victim

    suspects: tuple[Suspect, Suspect, Suspect, Suspect]

    initial_evidence: tuple[Evidence, ...] = ()

    @model_validator(mode="after")
    def validate_unique_ids(self) -> "CaseManifest":
        suspect_ids = [suspect.id for suspect in self.suspects]

        if len(suspect_ids) != len(set(suspect_ids)):
            raise ValueError("suspect IDs must be unique")

        evidence_ids = [
            evidence.id
            for evidence in self.initial_evidence
        ]

        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("evidence IDs must be unique")

        return self