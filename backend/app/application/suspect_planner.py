from app.application.ai_ports import (
    LLMError,
    StructuredLLMClient,
)
from app.domain.strategy import (
    LegalStrategy,
    StrategyProposal,
    StrategySpace,
    StrategyTactic,
    SuspectPlan,
)

STRATEGY_SYSTEM_PROMPT = """
You select one suspect response strategy.

You may select only a strategy contained in the supplied
strategy space.

You may select only fact IDs permitted by that strategy.
Do not invent strategy IDs or fact IDs.
Do not produce dialogue.
Do not add facts, explanations, or claims.
Return only the structured strategy proposal.
""".strip()

class SuspectPlanningError(ValueError):
    """Base error for invalid suspect plans."""


class IllegalStrategyError(SuspectPlanningError):
    """Raised when the model selects a forbidden strategy."""


class IllegalStrategyFactError(SuspectPlanningError):
    """Raised when the model selects a forbidden fact."""


class SuspectPlanner:
    def __init__(
        self,
        *,
        llm_client: StructuredLLMClient,
    ) -> None:
        self._llm_client = llm_client

    async def plan(
        self,
        *,
        detective_question: str,
        strategy_space: StrategySpace,
    ) -> SuspectPlan:
        normalized_question = detective_question.strip()

        if not normalized_question:
            return self._fallback(strategy_space)

        user_prompt = (
            "<strategy_space>\n"
            f"{strategy_space.model_dump_json(indent=2)}\n"
            "</strategy_space>\n\n"
            "<detective_question>\n"
            f"{normalized_question}\n"
            "</detective_question>"
        )

        try:
            proposal = (
                await self._llm_client.generate_structured(
                    system_prompt=STRATEGY_SYSTEM_PROMPT,
                    user_prompt=user_prompt,
                    output_type=StrategyProposal,
                )
            )
        except LLMError:
            return self._fallback(strategy_space)

        return self._validate_proposal(
            proposal=proposal,
            strategy_space=strategy_space,
        )

    @staticmethod
    def _validate_proposal(
        *,
        proposal: StrategyProposal,
        strategy_space: StrategySpace,
    ) -> SuspectPlan:
        strategies_by_id = {
            strategy.id: strategy
            for strategy in strategy_space.strategies
        }

        strategy = strategies_by_id.get(
            proposal.strategy_id
        )

        if strategy is None:
            raise IllegalStrategyError(
                "The model selected a strategy outside "
                "the legal strategy space: "
                f"{proposal.strategy_id!r}."
            )

        selected_fact_ids = set(
            proposal.fact_ids
        )
        permitted_fact_ids = set(
            strategy.permitted_fact_ids
        )

        forbidden_fact_ids = (
            selected_fact_ids
            - permitted_fact_ids
        )

        if forbidden_fact_ids:
            raise IllegalStrategyFactError(
                "The model selected facts forbidden by "
                f"{strategy.id!r}: "
                f"{sorted(forbidden_fact_ids)}."
            )

        selected_facts = tuple(
            fact
            for fact in strategy_space.facts
            if fact.id in selected_fact_ids
        )

        return SuspectPlan(
            suspect_id=strategy_space.suspect_id,
            strategy_id=strategy.id,
            tactic=strategy.tactic,
            selected_facts=selected_facts,
            used_fallback=False,
        )

    @staticmethod
    def _fallback(
        strategy_space: StrategySpace,
    ) -> SuspectPlan:
        refusal = _find_refusal(
            strategy_space.strategies
        )

        return SuspectPlan(
            suspect_id=strategy_space.suspect_id,
            strategy_id=refusal.id,
            tactic=refusal.tactic,
            selected_facts=(),
            used_fallback=True,
        )

def _find_refusal(
    strategies: tuple[LegalStrategy, ...],
) -> LegalStrategy:
    refusal = next(
        (
            strategy
            for strategy in strategies
            if strategy.tactic
            is StrategyTactic.REFUSE
        ),
        None,
    )

    if refusal is None:
        raise SuspectPlanningError(
            "Every strategy space must include a safe "
            "refusal strategy."
        )

    return refusal