from collections.abc import Collection

from app.domain.evidence import Evidence
from app.domain.suspect import Suspect
from app.domain.timeline import Timeline
from app.domain.unlock import (
    EvidenceUnlockRule,
    QuestionUnlockRule,
    StartingUnlockRule,
    UnlockRule,
)

class EvidenceConsistencyError(ValueError):
    """Raised when evidence causality or unlock rules are invalid."""


def validate_evidence(
    *,
    evidence_items: Collection[Evidence],
    suspects: Collection[Suspect],
    timeline: Timeline,
    critical_evidence_ids: Collection[str],
) -> None:
    evidence_by_id = {
        evidence.id: evidence
        for evidence in evidence_items
    }

    suspect_ids = {
        suspect.id
        for suspect in suspects
    }

    timeline_event_ids = {
        event.id
        for event in timeline.events
    }

    critical_ids = set(critical_evidence_ids)

    unknown_critical_ids = (
        critical_ids
        - set(evidence_by_id)
    )

    if unknown_critical_ids:
        raise EvidenceConsistencyError(
            "critical evidence references unknown evidence: "
            f"{sorted(unknown_critical_ids)}"
        )

    for evidence in evidence_items:
        _validate_source_event(
            evidence=evidence,
            timeline_event_ids=timeline_event_ids,
        )

        for rule in evidence.unlock_rules:
            _validate_rule_references(
                evidence=evidence,
                rule=rule,
                evidence_ids=set(evidence_by_id),
                suspect_ids=suspect_ids,
            )

    reachable_ids = reachable_evidence_ids(
        evidence_items,
    )

    unreachable_critical_ids = (
        critical_ids
        - reachable_ids
    )

    if unreachable_critical_ids:
        raise EvidenceConsistencyError(
            "critical evidence has no reachable unlock path: "
            f"{sorted(unreachable_critical_ids)}"
        )


def reachable_evidence_ids(
    evidence_items: Collection[Evidence],
) -> set[str]:
    """
    Return evidence reachable through at least one legal unlock path.

    Unlock rules on one evidence item are alternatives: satisfying any
    one rule makes that item reachable.
    """
    reachable: set[str] = set()
    evidence_by_id = {
        evidence.id: evidence
        for evidence in evidence_items
    }

    changed = True
    while changed:
        changed = False

        for evidence_id, evidence in evidence_by_id.items():
            if evidence_id in reachable:
                continue

            if any(
                _rule_is_reachable(
                    rule,
                    reachable_evidence_ids=reachable,
                )
                for rule in evidence.unlock_rules
            ):
                reachable.add(evidence_id)
                changed = True

    return reachable

def _validate_source_event(
    *,
    evidence: Evidence,
    timeline_event_ids: set[str],
) -> None:
    if evidence.source_event_id is None:
        raise EvidenceConsistencyError(
            f"evidence '{evidence.id}' has no source event"
        )

    if evidence.source_event_id not in timeline_event_ids:
        raise EvidenceConsistencyError(
            f"evidence '{evidence.id}' references unknown source "
            f"event '{evidence.source_event_id}'"
        )


def _validate_rule_references(
    *,
    evidence: Evidence,
    rule: UnlockRule,
    evidence_ids: set[str],
    suspect_ids: set[str],
) -> None:
    match rule:
        case StartingUnlockRule():
            return

        case QuestionUnlockRule():
            if rule.suspect_id not in suspect_ids:
                raise EvidenceConsistencyError(
                    f"evidence '{evidence.id}' unlock rule references "
                    f"unknown suspect '{rule.suspect_id}'"
                )

        case EvidenceUnlockRule():
            if rule.evidence_id not in evidence_ids:
                raise EvidenceConsistencyError(
                    f"evidence '{evidence.id}' unlock rule references "
                    f"unknown evidence '{rule.evidence_id}'"
                )

def _rule_is_reachable(
    rule: UnlockRule,
    *,
    reachable_evidence_ids: set[str],
) -> bool:
    match rule:
        case StartingUnlockRule():
            return True

        case QuestionUnlockRule():
            return True

        case EvidenceUnlockRule():
            return rule.evidence_id in reachable_evidence_ids

    raise AssertionError(
        f"Unhandled unlock rule: {rule!r}"
    )