from enum import Enum
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

ActorId = Annotated[
    str,
    Field(pattern=r"^(?:suspect|victim)_[a-z0-9_]+$"),
]

LocationId = Annotated[
    str,
    Field(pattern=r"^location_[a-z0-9_]+$"),
]

class ClockTime(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    hour: int = Field(
        ge=0,
        le=23,
    )
    minute: int = Field(
        ge=0,
        le=59,
    )

    @property
    def minute_of_day(self) -> int:
        return (self.hour * 60) + self.minute

    def __str__(self) -> str:
        return f"{self.hour:02d}:{self.minute:02d}"


class TimeInterval(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    start: ClockTime
    end: ClockTime

    @model_validator(mode="after")
    def validate_end_is_after_start(self) -> "TimeInterval":
        if self.end.minute_of_day <= self.start.minute_of_day:
            raise ValueError(
                "time interval end must be after its start"
            )

        return self

    def overlaps(self, other: "TimeInterval") -> bool:
        return (
            self.start.minute_of_day < other.end.minute_of_day
            and other.start.minute_of_day < self.end.minute_of_day
        )

    def contains(self, other: "TimeInterval") -> bool:
        return (
            self.start.minute_of_day
            <= other.start.minute_of_day
            and other.end.minute_of_day
            <= self.end.minute_of_day
        )


class TimelineEventKind(str, Enum):
    PRESENCE = "presence"
    MURDER = "murder"


class TimelineLocation(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    id: LocationId
    name: str = Field(
        min_length=1,
        max_length=120,
    )


class TimelineEvent(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    id: str = Field(
        pattern=r"^timeline_event_[a-z0-9_]+$",
    )
    kind: TimelineEventKind
    description: str = Field(
        min_length=1,
        max_length=500,
    )
    actor_ids: tuple[ActorId, ...] = Field(
        min_length=1,
    )
    location_id: LocationId
    interval: TimeInterval

    @field_validator("actor_ids")
    @classmethod
    def validate_unique_actor_ids(
        cls,
        actor_ids: tuple[str, ...],
    ) -> tuple[str, ...]:
        if len(actor_ids) != len(set(actor_ids)):
            raise ValueError(
                "timeline event actor IDs must be unique"
            )

        return actor_ids


class Timeline(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    murder_window: TimeInterval

    locations: tuple[TimelineLocation, ...] = Field(
        min_length=1,
    )

    events: tuple[TimelineEvent, ...] = Field(
        min_length=1,
    )

    @model_validator(mode="after")
    def validate_ids_and_location_references(self) -> "Timeline":
        location_ids = [
            location.id
            for location in self.locations
        ]

        if len(location_ids) != len(set(location_ids)):
            raise ValueError(
                "timeline location IDs must be unique"
            )

        event_ids = [
            event.id
            for event in self.events
        ]

        if len(event_ids) != len(set(event_ids)):
            raise ValueError(
                "timeline event IDs must be unique"
            )

        unknown_location_ids = {
            event.location_id
            for event in self.events
            if event.location_id not in location_ids
        }

        if unknown_location_ids:
            raise ValueError(
                "timeline events reference unknown locations: "
                f"{sorted(unknown_location_ids)}"
            )

        return self