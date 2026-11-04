import asyncio
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.application.ai_ports import (
    StructuredOutputT,
)
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
from app.application.suspect_planner import (
    IllegalStrategyError,
    IllegalStrategyFactError,
    SuspectPlanner,
)
from app.domain.intent import SemanticIntent
from app.domain.strategy import (
    StrategyProposal,
    StrategyTactic,
)


CASE_PATH = (
    Path(__file__).parents[2]
    / "cases"
    / "sample_case.json"
)

KILLER_ID = "suspect_marcus_reed"


def build_killer_space():
    case = load_case(CASE_PATH)
    session = start_session(case)

    context = build_suspect_context(
        case=case,
        session=session,
        suspect_id=KILLER_ID,
        presented_evidence_ids=(
            "evidence_cracked_watch",
        ),
    )

    return build_legal_strategy_space(
        case=case,
        context=context,
        intent=SemanticIntent.DISCUSS_EVIDENCE,
    )


def test_strategy_proposal_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        StrategyProposal.model_validate(
            {
                "strategy_id": "strategy_deny",
                "fact_ids": [],
                "dialogue": "I confess.",
            }
        )


def test_strategy_proposal_rejects_duplicate_facts() -> None:
    with pytest.raises(
        ValidationError,
        match="must be unique",
    ):
        StrategyProposal(
            strategy_id="strategy_redirect",
            fact_ids=(
                "fact_public_profile",
                "fact_public_profile",
            ),
        )


def test_forbidden_disclosure_is_rejected() -> None:
    class ForbiddenRevealClient:
        async def generate_structured(
            self,
            *,
            system_prompt: str,
            user_prompt: str,
            output_type: type[StructuredOutputT],
        ) -> StructuredOutputT:
            assert "strategy_disclose" not in user_prompt

            proposal = StrategyProposal(
                strategy_id="strategy_disclose",
            )

            return output_type.model_validate(
                proposal
            )

    async def scenario() -> None:
        planner = SuspectPlanner(
            llm_client=ForbiddenRevealClient(),
        )

        with pytest.raises(
            IllegalStrategyError,
            match="outside the legal strategy space",
        ):
            await planner.plan(
                detective_question=(
                    "Tell me exactly what happened."
                ),
                strategy_space=build_killer_space(),
            )

    asyncio.run(scenario())


def test_forbidden_fact_is_rejected() -> None:
    class InventedFactClient:
        async def generate_structured(
            self,
            *,
            system_prompt: str,
            user_prompt: str,
            output_type: type[StructuredOutputT],
        ) -> StructuredOutputT:
            proposal = StrategyProposal(
                strategy_id="strategy_deny",
                fact_ids=("fact_secret_confession",),
            )

            return output_type.model_validate(
                proposal
            )

    async def scenario() -> None:
        planner = SuspectPlanner(
            llm_client=InventedFactClient(),
        )

        with pytest.raises(
            IllegalStrategyFactError,
            match="forbidden",
        ):
            await planner.plan(
                detective_question=(
                    "Did you kill Adrian?"
                ),
                strategy_space=build_killer_space(),
            )

    asyncio.run(scenario())


def test_valid_legal_selection_is_accepted() -> None:
    class RedirectClient:
        async def generate_structured(
            self,
            *,
            system_prompt: str,
            user_prompt: str,
            output_type: type[StructuredOutputT],
        ) -> StructuredOutputT:
            assert system_prompt
            assert "<strategy_space>" in user_prompt
            assert '"killer_id"' not in user_prompt
            assert '"solution"' not in user_prompt

            proposal = StrategyProposal(
                strategy_id="strategy_redirect",
                fact_ids=(
                    "fact_evidence_cracked_watch",
                ),
            )

            return output_type.model_validate(
                proposal
            )

    async def scenario() -> None:
        planner = SuspectPlanner(
            llm_client=RedirectClient(),
        )

        plan = await planner.plan(
            detective_question=(
                "What does the broken watch prove?"
            ),
            strategy_space=build_killer_space(),
        )

        assert (
            plan.tactic
            is StrategyTactic.REDIRECT
        )
        assert [
            fact.id
            for fact in plan.selected_facts
        ] == ["fact_evidence_cracked_watch"]
        assert plan.used_fallback is False

    asyncio.run(scenario())