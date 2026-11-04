from pathlib import Path

from app.application.case_loader import load_case
from app.application.investigation_service import (
    start_session,
)
from app.application.legal_strategies import (
    build_legal_strategy_space,
)
from app.application.suspect_context import (
    build_suspect_context,
)
from app.domain.intent import SemanticIntent
from app.domain.strategy import StrategyTactic


CASE_PATH = (
    Path(__file__).parents[2]
    / "cases"
    / "sample_case.json"
)

KILLER_ID = "suspect_marcus_reed"
INNOCENT_ID = "suspect_maya_sen"


def build_space(
    suspect_id: str,
    intent: SemanticIntent = SemanticIntent.ASK_ALIBI,
):
    case = load_case(CASE_PATH)
    session = start_session(case)

    context = build_suspect_context(
        case=case,
        session=session,
        suspect_id=suspect_id,
        presented_evidence_ids=(
            "evidence_cracked_watch",
        ),
    )

    return build_legal_strategy_space(
        case=case,
        context=context,
        intent=intent,
    )


def tactics_for(suspect_id: str) -> set[StrategyTactic]:
    return {
        strategy.tactic
        for strategy in build_space(
            suspect_id
        ).strategies
    }


def test_innocent_can_disclose_but_cannot_evade() -> None:
    tactics = tactics_for(INNOCENT_ID)

    assert StrategyTactic.DISCLOSE in tactics
    assert StrategyTactic.REDIRECT in tactics
    assert StrategyTactic.REFUSE in tactics

    assert StrategyTactic.DENY not in tactics
    assert StrategyTactic.EVADE not in tactics


def test_killer_can_evade_but_cannot_disclose() -> None:
    tactics = tactics_for(KILLER_ID)

    assert StrategyTactic.DENY in tactics
    assert StrategyTactic.EVADE in tactics
    assert StrategyTactic.REDIRECT in tactics
    assert StrategyTactic.REFUSE in tactics

    assert StrategyTactic.DISCLOSE not in tactics


def test_unknown_intent_allows_only_refusal() -> None:
    space = build_space(
        INNOCENT_ID,
        intent=SemanticIntent.UNKNOWN,
    )

    assert [
        strategy.tactic
        for strategy in space.strategies
    ] == [StrategyTactic.REFUSE]


def test_strategy_facts_come_from_safe_context() -> None:
    space = build_space(KILLER_ID)

    serialized_space = space.model_dump_json()

    assert "fact_public_profile" in serialized_space
    assert "fact_relationship" in serialized_space
    assert "fact_evidence_cracked_watch" in serialized_space

    assert '"killer_id"' not in serialized_space
    assert '"solution"' not in serialized_space
    assert '"motive"' not in serialized_space
    assert '"method"' not in serialized_space


def test_strategy_space_is_deterministic() -> None:
    first = build_space(INNOCENT_ID)
    second = build_space(INNOCENT_ID)

    assert first == second
    assert (
        first.model_dump_json(indent=2)
        == second.model_dump_json(indent=2)
    )