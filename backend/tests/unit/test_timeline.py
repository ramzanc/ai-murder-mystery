import pytest
from pydantic import ValidationError

from app.domain.timeline import (
    ClockTime,
    TimeInterval,
    Timeline,
    TimelineEvent,
    TimelineEventKind,
    TimelineLocation,
)
from app.validation.timeline import (
    TimelineConsistencyError,
    validate_timeline,
)


def interval(
    start_hour: int,
    start_minute: int,
    end_hour: int,
    end_minute: int,
) -> TimeInterval:
    return TimeInterval(
        start=ClockTime(
            hour=start_hour,
            minute=start_minute,
        ),
        end=ClockTime(
            hour=end_hour,
            minute=end_minute,
        ),
    )


def event(
    event_id: str,
    *,
    kind: TimelineEventKind,
    actor_ids: tuple[str, ...],
    location_id: str,
    event_interval: TimeInterval,
) -> TimelineEvent:
    return TimelineEvent(
        id=event_id,
        kind=kind,
        description=f"Timeline event {event_id}.",
        actor_ids=actor_ids,
        location_id=location_id,
        interval=event_interval,
    )


def make_timeline(
    events: tuple[TimelineEvent, ...],
) -> Timeline:
    return Timeline(
        murder_window=interval(
            22,
            0,
            23,
            0,
        ),
        locations=(
            TimelineLocation(
                id="location_study",
                name="Study",
            ),
            TimelineLocation(
                id="location_hall",
                name="Hall",
            ),
        ),
        events=events,
    )


def validate_test_timeline(
    timeline: Timeline,
) -> None:
    validate_timeline(
        timeline,
        valid_actor_ids={
            "victim_one",
            "suspect_one",
            "suspect_two",
        },
        required_murder_actor_ids={
            "victim_one",
            "suspect_one",
        },
    )


def test_consistent_timeline_passes_validation() -> None:
    timeline = make_timeline(
        (
            event(
                "timeline_event_before",
                kind=TimelineEventKind.PRESENCE,
                actor_ids=("suspect_one",),
                location_id="location_hall",
                event_interval=interval(
                    22,
                    0,
                    22,
                    10,
                ),
            ),
            event(
                "timeline_event_murder",
                kind=TimelineEventKind.MURDER,
                actor_ids=(
                    "victim_one",
                    "suspect_one",
                ),
                location_id="location_study",
                event_interval=interval(
                    22,
                    10,
                    22,
                    11,
                ),
            ),
            event(
                "timeline_event_after",
                kind=TimelineEventKind.PRESENCE,
                actor_ids=("suspect_one",),
                location_id="location_hall",
                event_interval=interval(
                    22,
                    11,
                    22,
                    20,
                ),
            ),
            event(
                "timeline_event_second_suspect",
                kind=TimelineEventKind.PRESENCE,
                actor_ids=("suspect_two",),
                location_id="location_hall",
                event_interval=interval(
                    22,
                    0,
                    22,
                    20,
                ),
            ),
        )
    )

    validate_test_timeline(timeline)


def test_actor_cannot_be_in_two_locations_at_once() -> None:
    timeline = make_timeline(
        (
            event(
                "timeline_event_murder",
                kind=TimelineEventKind.MURDER,
                actor_ids=(
                    "victim_one",
                    "suspect_one",
                ),
                location_id="location_study",
                event_interval=interval(
                    22,
                    10,
                    22,
                    12,
                ),
            ),
            event(
                "timeline_event_impossible_alibi",
                kind=TimelineEventKind.PRESENCE,
                actor_ids=("suspect_one",),
                location_id="location_hall",
                event_interval=interval(
                    22,
                    11,
                    22,
                    15,
                ),
            ),
        )
    )

    with pytest.raises(
        TimelineConsistencyError,
        match="two locations at the same time",
    ):
        validate_test_timeline(timeline)


def test_event_actor_must_exist_in_case() -> None:
    timeline = make_timeline(
        (
            event(
                "timeline_event_murder",
                kind=TimelineEventKind.MURDER,
                actor_ids=(
                    "victim_one",
                    "suspect_unknown",
                ),
                location_id="location_study",
                event_interval=interval(
                    22,
                    10,
                    22,
                    11,
                ),
            ),
        )
    )

    with pytest.raises(
        TimelineConsistencyError,
        match="unknown actors",
    ):
        validate_test_timeline(timeline)


def test_event_location_must_exist_in_timeline() -> None:
    unknown_location_event = event(
        "timeline_event_murder",
        kind=TimelineEventKind.MURDER,
        actor_ids=(
            "victim_one",
            "suspect_one",
        ),
        location_id="location_unknown",
        event_interval=interval(
            22,
            10,
            22,
            11,
        ),
    )

    with pytest.raises(
        ValidationError,
        match="unknown locations",
    ):
        make_timeline((unknown_location_event,))


def test_murder_must_be_inside_declared_window() -> None:
    timeline = make_timeline(
        (
            event(
                "timeline_event_murder",
                kind=TimelineEventKind.MURDER,
                actor_ids=(
                    "victim_one",
                    "suspect_one",
                ),
                location_id="location_study",
                event_interval=interval(
                    21,
                    58,
                    21,
                    59,
                ),
            ),
        )
    )

    with pytest.raises(
        TimelineConsistencyError,
        match="inside the declared murder window",
    ):
        validate_test_timeline(timeline)


def test_timeline_requires_exactly_one_murder_event() -> None:
    timeline = make_timeline(
        (
            event(
                "timeline_event_presence",
                kind=TimelineEventKind.PRESENCE,
                actor_ids=("suspect_one",),
                location_id="location_hall",
                event_interval=interval(
                    22,
                    10,
                    22,
                    11,
                ),
            ),
        )
    )

    with pytest.raises(
        TimelineConsistencyError,
        match="exactly one murder event",
    ):
        validate_test_timeline(timeline)