from pathlib import Path

import pytest
from pydantic import ValidationError

from app.application.case_loader import load_case
from app.domain.evidence import Evidence, EvidenceKind
from app.domain.investigation import QuestionTopic
from app.domain.suspect import Suspect
from app.domain.timeline import (
    ClockTime,
    TimeInterval,
    Timeline,
    TimelineEvent,
    TimelineEventKind,
    TimelineLocation,
)
from app.domain.unlock import (
    EvidenceUnlockRule,
    QuestionUnlockRule,
    StartingUnlockRule,
)
from app.validation.evidence import (
    EvidenceConsistencyError,
    reachable_evidence_ids,
    validate_evidence,
)


BACKEND_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_CASE_PATH = (
    BACKEND_ROOT
    / "cases"
    / "sample_case.json"
)


def make_suspect(
    suspect_id: str = "suspect_one",
) -> Suspect:
    return Suspect(
        id=suspect_id,
        name="Test Suspect",
        age=35,
        occupation="Accountant",
        relationship_to_victim="Business partner",
        public_profile="The suspect attended the gathering.",
    )


def make_timeline() -> Timeline:
    return Timeline(
        murder_window=TimeInterval(
            start=ClockTime(hour=21, minute=0),
            end=ClockTime(hour=22, minute=0),
        ),
        locations=(
            TimelineLocation(
                id="location_office",
                name="Office",
            ),
        ),
        events=(
            TimelineEvent(
                id="timeline_event_murder",
                kind=TimelineEventKind.MURDER,
                description="The victim was killed in the office.",
                actor_ids=(
                    "victim_one",
                    "suspect_one",
                ),
                location_id="location_office",
                interval=TimeInterval(
                    start=ClockTime(hour=21, minute=30),
                    end=ClockTime(hour=21, minute=31),
                ),
            ),
        ),
    )


def make_evidence(
    evidence_id: str,
    *,
    source_event_id: str | None = "timeline_event_murder",
    unlock_rules: tuple = (),
) -> Evidence:
    return Evidence(
        id=evidence_id,
        title=f"Clue {evidence_id}",
        description="A clue relevant to the investigation.",
        kind=EvidenceKind.PHYSICAL,
        source_event_id=source_event_id,
        unlock_rules=unlock_rules,
    )


def validate_test_evidence(
    evidence_items: tuple[Evidence, ...],
    *,
    critical_evidence_ids: tuple[str, ...],
) -> None:
    validate_evidence(
        evidence_items=evidence_items,
        suspects=(make_suspect(),),
        timeline=make_timeline(),
        critical_evidence_ids=critical_evidence_ids,
    )


def test_discriminated_union_constructs_correct_rule_types() -> None:
    evidence = Evidence.model_validate(
        {
            "id": "evidence_three_paths",
            "title": "Three Paths",
            "description": "A clue with three typed unlock rules.",
            "kind": "document",
            "source_event_id": "timeline_event_murder",
            "unlock_rules": [
                {
                    "kind": "starting",
                },
                {
                    "kind": "question",
                    "suspect_id": "suspect_one",
                    "intent": "alibi",
                },
                {
                    "kind": "evidence",
                    "evidence_id": "evidence_other",
                },
            ],
        }
    )

    assert isinstance(
        evidence.unlock_rules[0],
        StartingUnlockRule,
    )
    assert isinstance(
        evidence.unlock_rules[1],
        QuestionUnlockRule,
    )
    assert isinstance(
        evidence.unlock_rules[2],
        EvidenceUnlockRule,
    )


def test_unknown_unlock_kind_is_rejected() -> None:
    with pytest.raises(
        ValidationError,
        match="union_tag_invalid",
    ):
        Evidence.model_validate(
            {
                "id": "evidence_invalid_rule",
                "title": "Invalid Rule",
                "description": "This rule kind is unsupported.",
                "kind": "physical",
                "source_event_id": "timeline_event_murder",
                "unlock_rules": [
                    {
                        "kind": "magic_keyword",
                    },
                ],
            }
        )


def test_unknown_question_intent_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Evidence.model_validate(
            {
                "id": "evidence_invalid_intent",
                "title": "Invalid Intent",
                "description": "This intent is unsupported.",
                "kind": "testimony",
                "source_event_id": "timeline_event_murder",
                "unlock_rules": [
                    {
                        "kind": "question",
                        "suspect_id": "suspect_one",
                        "intent": "confess_immediately",
                    },
                ],
            }
        )


def test_evidence_requires_a_source_event() -> None:
    evidence = make_evidence(
        "evidence_missing_source",
        source_event_id=None,
        unlock_rules=(StartingUnlockRule(),),
    )

    with pytest.raises(
        EvidenceConsistencyError,
        match="has no source event",
    ):
        validate_test_evidence(
            (evidence,),
            critical_evidence_ids=(evidence.id,),
        )


def test_source_event_must_exist_in_timeline() -> None:
    evidence = make_evidence(
        "evidence_unknown_source",
        source_event_id="timeline_event_missing",
        unlock_rules=(StartingUnlockRule(),),
    )

    with pytest.raises(
        EvidenceConsistencyError,
        match="unknown source event",
    ):
        validate_test_evidence(
            (evidence,),
            critical_evidence_ids=(evidence.id,),
        )


def test_question_rule_must_reference_case_suspect() -> None:
    evidence = make_evidence(
        "evidence_unknown_suspect",
        unlock_rules=(
            QuestionUnlockRule(
                suspect_id="suspect_missing",
                intent=QuestionTopic.ALIBI,
            ),
        ),
    )

    with pytest.raises(
        EvidenceConsistencyError,
        match="unknown suspect",
    ):
        validate_test_evidence(
            (evidence,),
            critical_evidence_ids=(evidence.id,),
        )


def test_evidence_rule_must_reference_case_evidence() -> None:
    evidence = make_evidence(
        "evidence_unknown_requirement",
        unlock_rules=(
            EvidenceUnlockRule(
                evidence_id="evidence_missing",
            ),
        ),
    )

    with pytest.raises(
        EvidenceConsistencyError,
        match="unknown evidence",
    ):
        validate_test_evidence(
            (evidence,),
            critical_evidence_ids=(evidence.id,),
        )


def test_critical_evidence_requires_reachable_path() -> None:
    first = make_evidence(
        "evidence_first",
        unlock_rules=(
            EvidenceUnlockRule(
                evidence_id="evidence_second",
            ),
        ),
    )
    second = make_evidence(
        "evidence_second",
        unlock_rules=(
            EvidenceUnlockRule(
                evidence_id="evidence_first",
            ),
        ),
    )

    with pytest.raises(
        EvidenceConsistencyError,
        match="no reachable unlock path",
    ):
        validate_test_evidence(
            (first, second),
            critical_evidence_ids=(first.id,),
        )


def test_evidence_chain_becomes_reachable_from_starting_clue() -> None:
    first = make_evidence(
        "evidence_first",
        unlock_rules=(StartingUnlockRule(),),
    )
    second = make_evidence(
        "evidence_second",
        unlock_rules=(
            EvidenceUnlockRule(
                evidence_id=first.id,
            ),
        ),
    )
    third = make_evidence(
        "evidence_third",
        unlock_rules=(
            EvidenceUnlockRule(
                evidence_id=second.id,
            ),
        ),
    )

    validate_test_evidence(
        (first, second, third),
        critical_evidence_ids=(third.id,),
    )

    assert reachable_evidence_ids(
        (first, second, third)
    ) == {
        first.id,
        second.id,
        third.id,
    }


def test_critical_evidence_can_have_multiple_legal_paths() -> None:
    starting_clue = make_evidence(
        "evidence_starting_clue",
        unlock_rules=(StartingUnlockRule(),),
    )
    critical_clue = make_evidence(
        "evidence_critical_clue",
        unlock_rules=(
            QuestionUnlockRule(
                suspect_id="suspect_one",
                intent=QuestionTopic.ALIBI,
            ),
            EvidenceUnlockRule(
                evidence_id=starting_clue.id,
            ),
        ),
    )

    validate_test_evidence(
        (starting_clue, critical_clue),
        critical_evidence_ids=(critical_clue.id,),
    )

    assert critical_clue.id in reachable_evidence_ids(
        (starting_clue, critical_clue)
    )


def test_sample_case_critical_evidence_is_reachable() -> None:
    case = load_case(SAMPLE_CASE_PATH)

    reachable_ids = reachable_evidence_ids(
        case.initial_evidence
    )

    assert set(
        case.solution.key_evidence_ids
    ) <= reachable_ids