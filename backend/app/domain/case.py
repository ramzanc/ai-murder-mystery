from enum import Enum

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

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


class CanonicalSolution(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    killer_id: str = Field(
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

    key_evidence_ids: tuple[str, ...] = Field(
        min_length=2,
        max_length=3,
    )

    explanation: str = Field(
        min_length=1,
        max_length=2000,
    )


class AccusationOptions(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    motives: tuple[str, ...] = Field(
        min_length=2,
        max_length=6,
    )
    methods: tuple[str, ...] = Field(
        min_length=2,
        max_length=6,
    )

    @field_validator("motives", "methods")
    @classmethod
    def validate_unique_nonblank_options(
        cls,
        options: tuple[str, ...],
    ) -> tuple[str, ...]:
        stripped_options = tuple(option.strip() for option in options)

        if any(not option for option in stripped_options):
            raise ValueError("accusation options must not be blank")

        normalized = [option.casefold() for option in stripped_options]

        if len(normalized) != len(set(normalized)):
            raise ValueError("accusation options must be unique")

        return stripped_options


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

    accusation_options: AccusationOptions
    solution: CanonicalSolution

    @model_validator(mode="after")
    def validate_references_and_unique_ids(self) -> "CaseManifest":
        suspect_ids = [suspect.id for suspect in self.suspects]

        if len(suspect_ids) != len(set(suspect_ids)):
            raise ValueError("suspect IDs must be unique")

        if self.solution.killer_id not in suspect_ids:
            raise ValueError(
                "solution killer_id must reference a case suspect"
            )

        if self.solution.motive not in self.accusation_options.motives:
            raise ValueError(
                "solution motive must be present in accusation options"
            )

        if self.solution.method not in self.accusation_options.methods:
            raise ValueError(
                "solution method must be present in accusation options"
            )

        evidence_ids = [
            evidence.id
            for evidence in self.initial_evidence
        ]

        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("evidence IDs must be unique")

        solution_evidence_ids = self.solution.key_evidence_ids

        if len(solution_evidence_ids) != len(set(solution_evidence_ids)):
            raise ValueError("solution key evidence IDs must be unique")

        unknown_solution_evidence = (
            set(solution_evidence_ids)
            - set(evidence_ids)
        )

        if unknown_solution_evidence:
            raise ValueError(
                "solution key evidence must reference case evidence: "
                f"{sorted(unknown_solution_evidence)}"
            )

        return self
