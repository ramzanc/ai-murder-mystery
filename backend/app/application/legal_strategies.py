from app.application.suspect_context import (
    SuspectContext,
)
from app.domain.case import CaseManifest
from app.domain.intent import SemanticIntent
from app.domain.strategy import (
    LegalStrategy,
    StrategyFact,
    StrategySpace,
    StrategyTactic,
)

class LegalStrategyError(ValueError):
    """Raised when a legal strategy space cannot be built."""


class StrategyContextMismatchError(
    LegalStrategyError
):
    """Raised when context and case do not match."""


def build_legal_strategy_space(
    *,
    case: CaseManifest,
    context: SuspectContext,
    intent: SemanticIntent,
) -> StrategySpace:
    if context.case_id != str(case.id):
        raise StrategyContextMismatchError(
            "The suspect context belongs to another case."
        )

    case_suspect_ids = {
        str(suspect.id)
        for suspect in case.suspects
    }

    if context.suspect_id not in case_suspect_ids:
        raise StrategyContextMismatchError(
            "The suspect context references an unknown "
            "case suspect."
        )

    facts = _build_strategy_facts(context)
    all_fact_ids = tuple(
        fact.id
        for fact in facts
    )

    if intent is SemanticIntent.UNKNOWN:
        strategies = (
            _refuse_strategy(),
        )
    elif (
        context.suspect_id
        == str(case.solution.killer_id)
    ):
        strategies = _killer_strategies(
            all_fact_ids=all_fact_ids,
        )
    else:
        strategies = _innocent_strategies(
            all_fact_ids=all_fact_ids,
        )

    return StrategySpace(
        suspect_id=context.suspect_id,
        facts=facts,
        strategies=strategies,
    )

def _build_strategy_facts(
    context: SuspectContext,
) -> tuple[StrategyFact, ...]:
    facts: list[StrategyFact] = [
        StrategyFact(
            id="fact_public_profile",
            statement=context.public_profile,
        ),
        StrategyFact(
            id="fact_relationship",
            statement=context.relationship_to_victim,
        ),
    ]

    facts.extend(
        StrategyFact(
            id=f"fact_known_{index}",
            statement=statement,
        )
        for index, statement in enumerate(
            context.known_facts,
            start=1,
        )
    )

    facts.extend(
        StrategyFact(
            id=f"fact_observation_{index}",
            statement=observation.description,
        )
        for index, observation in enumerate(
            context.observations,
            start=1,
        )
    )

    facts.extend(
        StrategyFact(
            id=f"fact_belief_{index}",
            statement=belief.statement,
        )
        for index, belief in enumerate(
            context.beliefs,
            start=1,
        )
    )

    facts.extend(
        StrategyFact(
            id=f"fact_evidence_{evidence.id.removeprefix('evidence_')}",
            statement=(
                f"{evidence.title}: "
                f"{evidence.description}"
            ),
        )
        for evidence in context.presented_evidence
    )

    return tuple(facts)


def _innocent_strategies(
    *,
    all_fact_ids: tuple[str, ...],
) -> tuple[LegalStrategy, ...]:
    return (
        LegalStrategy(
            id="strategy_disclose",
            tactic=StrategyTactic.DISCLOSE,
            instruction=(
                "Answer directly using only the selected "
                "permitted facts."
            ),
            permitted_fact_ids=all_fact_ids,
        ),
        LegalStrategy(
            id="strategy_redirect",
            tactic=StrategyTactic.REDIRECT,
            instruction=(
                "Redirect attention toward a relevant "
                "known fact without inventing information."
            ),
            permitted_fact_ids=all_fact_ids,
        ),
        _refuse_strategy(),
    )

def _killer_strategies(
    *,
    all_fact_ids: tuple[str, ...],
) -> tuple[LegalStrategy, ...]:
    return (
        LegalStrategy(
            id="strategy_deny",
            tactic=StrategyTactic.DENY,
            instruction=(
                "Deny the accusation without introducing "
                "new factual claims."
            ),
        ),
        LegalStrategy(
            id="strategy_evade",
            tactic=StrategyTactic.EVADE,
            instruction=(
                "Avoid answering directly and do not reveal "
                "hidden culpability."
            ),
        ),
        LegalStrategy(
            id="strategy_redirect",
            tactic=StrategyTactic.REDIRECT,
            instruction=(
                "Redirect attention using only selected "
                "permitted facts."
            ),
            permitted_fact_ids=all_fact_ids,
        ),
        _refuse_strategy(),
    )

def _refuse_strategy() -> LegalStrategy:
    return LegalStrategy(
        id="strategy_refuse",
        tactic=StrategyTactic.REFUSE,
        instruction=(
            "Refuse to answer without adding factual claims."
        ),
    )