import re
from enum import StrEnum
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from app.application.reveal import CaseReveal
from app.application.scoring import TheoryScore
from app.domain.case import CaseManifest
from app.domain.evidence import Evidence
from app.domain.investigation import (
    InvestigationSession,
    QuestionEvent,
    QuestionTopic,
)
from app.domain.theory import Theory

class ApiModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

class PublicDossierResponse(ApiModel):
    summary: str
    location: str
    incident_time: str

class PublicVictimResponse(ApiModel):
    id: str
    name: str
    age: int
    public_profile: str

class PublicSuspectResponse(ApiModel):
    id: str
    name: str
    age: int
    occupation: str
    relationship_to_victim: str
    public_profile: str

class PublicEvidenceResponse(ApiModel):
    id: str
    title: str
    description: str
    kind: str

    @classmethod
    def from_domain(
        cls,
        evidence: Evidence,
    ) -> "PublicEvidenceResponse":
        return cls(
            id=str(evidence.id),
            title=evidence.title,
            description=evidence.description,
            kind=evidence.kind.value,
        )


class AccusationOptionsResponse(ApiModel):
    motives: tuple[str, ...]
    methods: tuple[str, ...]


class PublicCaseResponse(ApiModel):
    id: str
    title: str
    difficulty: str
    dossier: PublicDossierResponse
    victim: PublicVictimResponse
    suspects: tuple[PublicSuspectResponse, ...]
    initial_evidence: tuple[PublicEvidenceResponse, ...]
    accusation_options: AccusationOptionsResponse

    @classmethod
    def from_domain(
        cls,
        case: CaseManifest,
    ) -> "PublicCaseResponse":
        return cls(
            id=str(case.id),
            title=case.title,
            difficulty=case.difficulty.value,
            dossier=PublicDossierResponse(
                summary=case.dossier.summary,
                location=case.dossier.location,
                incident_time=case.dossier.incident_time,
            ),
            victim=PublicVictimResponse(
                id=str(case.victim.id),
                name=case.victim.name,
                age=case.victim.age,
                public_profile=case.victim.public_profile,
            ),
            suspects=tuple(
                PublicSuspectResponse(
                    id=str(suspect.id),
                    name=suspect.name,
                    age=suspect.age,
                    occupation=suspect.occupation,
                    relationship_to_victim=(
                        suspect.relationship_to_victim
                    ),
                    public_profile=suspect.public_profile,
                )
                for suspect in case.suspects
            ),
            initial_evidence=tuple(
                PublicEvidenceResponse.from_domain(evidence)
                for evidence in case.initial_evidence
            ),
            accusation_options=AccusationOptionsResponse(
                motives=case.accusation_options.motives,
                methods=case.accusation_options.methods,
            ),
        )


class CreateSessionRequest(ApiModel):
    case_id: str = Field(
        pattern=r"^case_[a-z0-9_]+$",
    )

class ApiQuestionTopic(StrEnum):
    ALIBI = "alibi"
    SECRET = "secret"


class AskQuestionRequest(ApiModel):
    suspect_id: str = Field(
        pattern=r"^suspect_[a-z0-9_]+$",
    )
    topic: ApiQuestionTopic

    def to_domain_topic(self) -> QuestionTopic:
        return QuestionTopic(self.topic.value)


class QuestionEventResponse(ApiModel):
    sequence: int
    suspect_id: str
    topic: str
    question: str
    answer: str

    @classmethod
    def from_domain(
        cls,
        event: QuestionEvent,
    ) -> "QuestionEventResponse":
        return cls(
            sequence=event.sequence,
            suspect_id=event.suspect_id,
            topic=event.topic.value,
            question=event.question,
            answer=event.answer,
        )


class SessionResponse(ApiModel):
    id: UUID
    case_id: str
    events: tuple[QuestionEventResponse, ...]
    discovered_evidence_ids: tuple[str, ...]
    is_finalized: bool
    official_score: int | None

    @classmethod
    def from_domain(
        cls,
        *,
        session_id: UUID,
        session: InvestigationSession,
    ) -> "SessionResponse":
        return cls(
            id=session_id,
            case_id=session.case_id,
            events=tuple(
                QuestionEventResponse.from_domain(event)
                for event in session.events
            ),
            discovered_evidence_ids=(
                session.discovered_evidence_ids
            ),
            is_finalized=session.is_finalized,
            official_score=session.official_score,
        )


class SubmitTheoryRequest(ApiModel):
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
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError(
                "evidence IDs must be unique"
            )

        for evidence_id in evidence_ids:
            if re.fullmatch(
                r"evidence_[a-z0-9_]+",
                evidence_id,
            ) is None:
                raise ValueError(
                    f"invalid evidence ID: {evidence_id}"
                )

        return evidence_ids

    def to_domain(self) -> Theory:
        return Theory(
            killer_id=self.killer_id,
            motive=self.motive,
            method=self.method,
            evidence_ids=self.evidence_ids,
        )


class TheoryScoreResponse(ApiModel):
    killer_correct: bool
    motive_correct: bool
    method_correct: bool
    matching_evidence_ids: tuple[str, ...]
    killer_points: int
    motive_points: int
    method_points: int
    evidence_points: int
    total_points: int
    solved: bool

    @classmethod
    def from_domain(
        cls,
        score: TheoryScore,
    ) -> "TheoryScoreResponse":
        return cls(
            killer_correct=score.killer_correct,
            motive_correct=score.motive_correct,
            method_correct=score.method_correct,
            matching_evidence_ids=(
                score.matching_evidence_ids
            ),
            killer_points=score.killer_points,
            motive_points=score.motive_points,
            method_points=score.method_points,
            evidence_points=score.evidence_points,
            total_points=score.total_points,
            solved=score.solved,
        )

class TheorySubmissionResponse(ApiModel):
    session: SessionResponse
    score: TheoryScoreResponse


class RevealEvidenceResponse(ApiModel):
    id: str
    title: str
    description: str


class CaseRevealResponse(ApiModel):
    killer_id: str
    killer_name: str
    motive: str
    method: str
    key_evidence: tuple[RevealEvidenceResponse, ...]
    explanation: str

    @classmethod
    def from_domain(
        cls,
        reveal: CaseReveal,
    ) -> "CaseRevealResponse":
        return cls(
            killer_id=reveal.killer_id,
            killer_name=reveal.killer_name,
            motive=reveal.motive,
            method=reveal.method,
            key_evidence=tuple(
                RevealEvidenceResponse(
                    id=evidence.id,
                    title=evidence.title,
                    description=evidence.description,
                )
                for evidence in reveal.key_evidence
            ),
            explanation=reveal.explanation,
        )
