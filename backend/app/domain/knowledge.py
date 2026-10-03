from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

TimelineEventId = Annotated[
    str,
    Field(pattern=r"^timeline_event_[a-z0-9_]+$"),
]

ObservationId = Annotated[
    str,
    Field(pattern=r"^observation_[a-z0-9_]+$"),
]

BeliefId = Annotated[
    str,
    Field(pattern=r"^belief_[a-z0-9_]+$"),
]

Confidence = Annotated[
    float,
    Field(ge=0.0, le=1.0),
]


class Observation(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    id: ObservationId
    source_event_id: TimelineEventId
    perceived_description: str = Field(
        min_length=1,
        max_length=1000,
    )
    confidence: Confidence


class Belief(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    id: BeliefId
    about_event_id: TimelineEventId
    statement: str = Field(
        min_length=1,
        max_length=1000,
    )
    confidence: Confidence
    based_on_observation_ids: tuple[
        ObservationId,
        ...,
    ] = Field(min_length=1)

    @field_validator("based_on_observation_ids")
    @classmethod
    def validate_unique_observation_ids(
        cls,
        observation_ids: tuple[str, ...],
    ) -> tuple[str, ...]:
        if len(observation_ids) != len(set(observation_ids)):
            raise ValueError(
                "belief observation IDs must be unique"
            )

        return observation_ids


class SuspectKnowledge(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    known_event_ids: tuple[TimelineEventId, ...] = ()
    observations: tuple[Observation, ...] = ()
    beliefs: tuple[Belief, ...] = ()

    @field_validator("known_event_ids")
    @classmethod
    def validate_unique_known_event_ids(
        cls,
        event_ids: tuple[str, ...],
    ) -> tuple[str, ...]:
        if len(event_ids) != len(set(event_ids)):
            raise ValueError(
                "known event IDs must be unique"
            )

        return event_ids

    @field_validator("observations")
    @classmethod
    def validate_unique_observation_ids(
        cls,
        observations: tuple[Observation, ...],
    ) -> tuple[Observation, ...]:
        observation_ids = [
            observation.id
            for observation in observations
        ]

        if len(observation_ids) != len(set(observation_ids)):
            raise ValueError(
                "observation IDs must be unique within a suspect"
            )

        return observations

    @field_validator("beliefs")
    @classmethod
    def validate_unique_belief_ids(
        cls,
        beliefs: tuple[Belief, ...],
    ) -> tuple[Belief, ...]:
        belief_ids = [
            belief.id
            for belief in beliefs
        ]

        if len(belief_ids) != len(set(belief_ids)):
            raise ValueError(
                "belief IDs must be unique within a suspect"
            )

        return beliefs