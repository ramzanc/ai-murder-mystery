import pytest

from app.domain.knowledge import (
    Belief,
    Observation,
    SuspectKnowledge,
)
from app.domain.suspect import Suspect
from app.domain.timeline import (
    ClockTime,
    TimeInterval,
    Timeline,
    TimelineEvent,
    TimelineEventKind,
    TimelineLocation,
)
from app.validation.knowledge import (
    KnowledgeConsistencyError,
    validate_knowledge,
)


def interval(
    start_minute: int = 0,
    end_minute: int = 5,
) -> TimeInterval:
    return TimeInterval(
        start=ClockTime(
            hour=22,
            minute=start_minute,
        ),
        end=ClockTime(
            hour=22,
            minute=end_minute,
        ),
    )


def event(
    event_id: str,
    *,
    actor_ids: tuple[str, ...],
    description: str = "A canonical event occurred.",
) -> TimelineEvent:
    return TimelineEvent(
        id=event_id,
        kind=TimelineEventKind.PRESENCE,
        description=description,
        actor_ids=actor_ids,
        location_id="location_dining_room",
        interval=interval(),
    )


def timeline_with(
    *events: TimelineEvent,
) -> Timeline:
    return Timeline(
        murder_window=interval(
            start_minute=0,
            end_minute=30,
        ),
        locations=(
            TimelineLocation(
                id="location_dining_room",
                name="Dining room",
            ),
        ),
        events=events,
    )


def suspect(
    suspect_id: str,
    *,
    knowledge: SuspectKnowledge | None = None,
) -> Suspect:
    return Suspect(
        id=suspect_id,
        name=suspect_id.replace("_", " ").title(),
        age=35,
        occupation="Guest",
        relationship_to_victim="Acquaintance",
        public_profile="A guest at the dinner.",
        knowledge=knowledge or SuspectKnowledge(),
    )


def test_two_suspects_can_perceive_same_event_differently() -> None:
    source_event = event(
        "timeline_event_marcus_departure",
        actor_ids=(
            "suspect_marcus",
            "suspect_maya",
            "suspect_daniel",
        ),
        description=(
            "Marcus left the dining room and walked toward "
            "the study."
        ),
    )
    timeline = timeline_with(source_event)

    maya_observation = Observation(
        id="observation_maya_departure",
        source_event_id=source_event.id,
        perceived_description=(
            "Marcus hurried away and appeared nervous."
        ),
        confidence=0.85,
    )
    daniel_observation = Observation(
        id="observation_daniel_departure",
        source_event_id=source_event.id,
        perceived_description=(
            "Marcus left calmly, probably to take a call."
        ),
        confidence=0.65,
    )

    maya = suspect(
        "suspect_maya",
        knowledge=SuspectKnowledge(
            observations=(maya_observation,),
            beliefs=(
                Belief(
                    id="belief_maya_confrontation",
                    about_event_id=source_event.id,
                    statement=(
                        "Marcus intended to confront Adrian."
                    ),
                    confidence=0.75,
                    based_on_observation_ids=(
                        maya_observation.id,
                    ),
                ),
            ),
        ),
    )
    daniel = suspect(
        "suspect_daniel",
        knowledge=SuspectKnowledge(
            observations=(daniel_observation,),
            beliefs=(
                Belief(
                    id="belief_daniel_phone_call",
                    about_event_id=source_event.id,
                    statement=(
                        "Marcus left to take a business call."
                    ),
                    confidence=0.60,
                    based_on_observation_ids=(
                        daniel_observation.id,
                    ),
                ),
            ),
        ),
    )

    validate_knowledge(
        suspects=(maya, daniel),
        timeline=timeline,
    )

    assert (
        maya_observation.source_event_id
        == daniel_observation.source_event_id
    )
    assert (
        maya_observation.perceived_description
        != daniel_observation.perceived_description
    )
    assert (
        maya.knowledge.beliefs[0].statement
        != daniel.knowledge.beliefs[0].statement
    )


def test_observation_must_reference_causal_event() -> None:
    timeline = timeline_with(
        event(
            "timeline_event_dinner",
            actor_ids=("suspect_maya",),
        )
    )
    maya = suspect(
        "suspect_maya",
        knowledge=SuspectKnowledge(
            observations=(
                Observation(
                    id="observation_unknown_source",
                    source_event_id="timeline_event_missing",
                    perceived_description="I saw something.",
                    confidence=0.50,
                ),
            ),
        ),
    )

    with pytest.raises(
        KnowledgeConsistencyError,
        match="unknown source event",
    ):
        validate_knowledge(
            suspects=(maya,),
            timeline=timeline,
        )


def test_suspect_must_be_present_to_observe_event() -> None:
    private_event = event(
        "timeline_event_private_conversation",
        actor_ids=("suspect_marcus",),
    )
    timeline = timeline_with(private_event)

    maya = suspect(
        "suspect_maya",
        knowledge=SuspectKnowledge(
            observations=(
                Observation(
                    id="observation_maya_private_conversation",
                    source_event_id=private_event.id,
                    perceived_description=(
                        "Marcus discussed the missing money."
                    ),
                    confidence=0.90,
                ),
            ),
        ),
    )

    with pytest.raises(
        KnowledgeConsistencyError,
        match="not present in that source event",
    ):
        validate_knowledge(
            suspects=(maya,),
            timeline=timeline,
        )


def test_private_fact_requires_information_source() -> None:
    private_event = event(
        "timeline_event_private_conversation",
        actor_ids=("suspect_marcus",),
    )
    timeline = timeline_with(private_event)

    maya = suspect(
        "suspect_maya",
        knowledge=SuspectKnowledge(
            known_event_ids=(private_event.id,),
        ),
    )

    with pytest.raises(
        KnowledgeConsistencyError,
        match="without an observation or direct participation",
    ):
        validate_knowledge(
            suspects=(maya,),
            timeline=timeline,
        )


def test_belief_cannot_use_another_suspects_observation() -> None:
    source_event = event(
        "timeline_event_shared_departure",
        actor_ids=(
            "suspect_maya",
            "suspect_daniel",
        ),
    )
    timeline = timeline_with(source_event)

    maya_observation = Observation(
        id="observation_maya_departure",
        source_event_id=source_event.id,
        perceived_description="Daniel left the room.",
        confidence=0.95,
    )

    maya = suspect(
        "suspect_maya",
        knowledge=SuspectKnowledge(
            observations=(maya_observation,),
        ),
    )
    daniel = suspect(
        "suspect_daniel",
        knowledge=SuspectKnowledge(
            beliefs=(
                Belief(
                    id="belief_daniel_from_maya",
                    about_event_id=source_event.id,
                    statement="Maya thinks I left the room.",
                    confidence=0.80,
                    based_on_observation_ids=(
                        maya_observation.id,
                    ),
                ),
            ),
        ),
    )

    with pytest.raises(
        KnowledgeConsistencyError,
        match="outside its own knowledge",
    ):
        validate_knowledge(
            suspects=(maya, daniel),
            timeline=timeline,
        )


def test_wrong_belief_does_not_change_canonical_truth() -> None:
    source_event = event(
        "timeline_event_marcus_departure",
        actor_ids=("suspect_marcus",),
        description="Marcus walked toward the study.",
    )
    timeline = timeline_with(source_event)
    original_timeline = timeline.model_dump()

    observation = Observation(
        id="observation_marcus_departure",
        source_event_id=source_event.id,
        perceived_description=(
            "I left the dining room for a phone call."
        ),
        confidence=1.0,
    )
    marcus = suspect(
        "suspect_marcus",
        knowledge=SuspectKnowledge(
            observations=(observation,),
            beliefs=(
                Belief(
                    id="belief_marcus_phone_call",
                    about_event_id=source_event.id,
                    statement=(
                        "I walked away only to take a phone call."
                    ),
                    confidence=1.0,
                    based_on_observation_ids=(
                        observation.id,
                    ),
                ),
            ),
        ),
    )

    validate_knowledge(
        suspects=(marcus,),
        timeline=timeline,
    )

    assert timeline.model_dump() == original_timeline
    assert (
        timeline.events[0].description
        == "Marcus walked toward the study."
    )
    assert (
        marcus.knowledge.beliefs[0].statement
        != timeline.events[0].description
    )