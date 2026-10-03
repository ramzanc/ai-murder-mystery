from collections.abc import Collection

from app.domain.suspect import Suspect
from app.domain.timeline import Timeline

class KnowledgeConsistencyError(ValueError):
    """Raised when suspect knowledge violates case truth boundaries."""


def validate_knowledge(
    *,
    suspects: Collection[Suspect],
    timeline: Timeline,
) -> None:
    events_by_id = {
        event.id: event
        for event in timeline.events
    }

    observation_owner_by_id: dict[str, str] = {}
    belief_owner_by_id: dict[str, str] = {}

    for suspect in suspects:
        for observation in suspect.knowledge.observations:
            previous_owner = observation_owner_by_id.get(
                observation.id
            )

            if previous_owner is not None:
                raise KnowledgeConsistencyError(
                    f"observation '{observation.id}' is owned by "
                    f"both '{previous_owner}' and '{suspect.id}'"
                )

            observation_owner_by_id[observation.id] = suspect.id

        for belief in suspect.knowledge.beliefs:
            previous_owner = belief_owner_by_id.get(belief.id)

            if previous_owner is not None:
                raise KnowledgeConsistencyError(
                    f"belief '{belief.id}' is owned by both "
                    f"'{previous_owner}' and '{suspect.id}'"
                )

            belief_owner_by_id[belief.id] = suspect.id

        for suspect in suspects:
            own_observations = {
                observation.id: observation
                for observation in suspect.knowledge.observations
            }

            observed_event_ids = {
                observation.source_event_id
                for observation in suspect.knowledge.observations
            }

            for observation in suspect.knowledge.observations:
                source_event = events_by_id.get(
                    observation.source_event_id
                )

                if source_event is None:
                    raise KnowledgeConsistencyError(
                        f"suspect '{suspect.id}' observation "
                        f"'{observation.id}' references unknown source "
                        f"event '{observation.source_event_id}'"
                    )

                if suspect.id not in source_event.actor_ids:
                    raise KnowledgeConsistencyError(
                        f"suspect '{suspect.id}' cannot observe "
                        f"'{source_event.id}' because the suspect is not "
                        "present in that source event"
                    )

            for known_event_id in suspect.knowledge.known_event_ids:
                known_event = events_by_id.get(known_event_id)

                if known_event is None:
                    raise KnowledgeConsistencyError(
                        f"suspect '{suspect.id}' knows unknown event "
                        f"'{known_event_id}'"
                    )

                has_direct_source = suspect.id in known_event.actor_ids
                has_observation_source = (
                    known_event_id in observed_event_ids
                )

                if not has_direct_source and not has_observation_source:
                    raise KnowledgeConsistencyError(
                        f"suspect '{suspect.id}' cannot know private "
                        f"event '{known_event_id}' without an "
                        "observation or direct participation source"
                    )

            for belief in suspect.knowledge.beliefs:
                if belief.about_event_id not in events_by_id:
                    raise KnowledgeConsistencyError(
                        f"suspect '{suspect.id}' belief '{belief.id}' "
                        f"references unknown event "
                        f"'{belief.about_event_id}'"
                    )

                missing_observation_ids = (
                    set(belief.based_on_observation_ids)
                    - set(own_observations)
                )

                if missing_observation_ids:
                    raise KnowledgeConsistencyError(
                        f"suspect '{suspect.id}' belief '{belief.id}' "
                        "references observations outside its own "
                        f"knowledge: {sorted(missing_observation_ids)}"
                    )
