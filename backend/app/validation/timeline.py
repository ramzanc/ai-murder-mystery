from collections.abc import Collection
from itertools import combinations

from app.domain.timeline import (
    Timeline,
    TimelineEventKind,
)

class TimelineConsistencyError(ValueError):
    """Raised when a structurally valid timeline is impossible."""


def validate_timeline(
    timeline: Timeline,
    *,
    valid_actor_ids: Collection[str],
    required_murder_actor_ids: Collection[str],
) -> None:
    known_actor_ids = set(valid_actor_ids)

    referenced_actor_ids = {
        actor_id
        for event in timeline.events
        for actor_id in event.actor_ids
    }

    unknown_actor_ids = referenced_actor_ids - known_actor_ids

    if unknown_actor_ids:
        raise TimelineConsistencyError(
            "timeline events reference unknown actors: "
            f"{sorted(unknown_actor_ids)}"
        )

    murder_events = [
        event
        for event in timeline.events
        if event.kind == TimelineEventKind.MURDER
    ]

    if len(murder_events) != 1:
        raise TimelineConsistencyError(
            "timeline must contain exactly one murder event"
        )

    murder_event = murder_events[0]

    missing_murder_actor_ids = (
        set(required_murder_actor_ids)
        - set(murder_event.actor_ids)
    )

    if missing_murder_actor_ids:
        raise TimelineConsistencyError(
            "murder event is missing required actors: "
            f"{sorted(missing_murder_actor_ids)}"
        )

    if not timeline.murder_window.contains(
        murder_event.interval
    ):
        raise TimelineConsistencyError(
            "murder event must lie inside the declared murder window"
        )

    for first_event, second_event in combinations(
        timeline.events,
        2,
    ):
        shared_actor_ids = (
            set(first_event.actor_ids)
            & set(second_event.actor_ids)
        )

        if not shared_actor_ids:
            continue

        if first_event.location_id == second_event.location_id:
            continue

        if not first_event.interval.overlaps(
            second_event.interval
        ):
            continue


        actor_id = sorted(shared_actor_ids)[0]

        raise TimelineConsistencyError(
            f"actor '{actor_id}' is in two locations at the "
            f"same time: '{first_event.location_id}' in "
            f"'{first_event.id}' and "
            f"'{second_event.location_id}' in "
            f"'{second_event.id}'"
        )