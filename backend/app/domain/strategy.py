from enum import StrEnum

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

class StrategyTactic(StrEnum):
    DENY = "deny"
    EVADE = "evade"
    DISCLOSE = "disclose"
    REDIRECT = "redirect"
    REFUSE = "refuse"

class StrategyFact(BaseModel):
    """One fact that the planner is allowed to consider."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    id: str = Field(
        pattern=r"^fact_[a-z0-9_]+$",
    )
    statement: str = Field(
        min_length=1,
        max_length=1000,
    )

class LegalStrategy(BaseModel):
    """One tactic Python has made available to the LLM."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    id: str = Field(
        pattern=r"^strategy_[a-z0-9_]+$",
    )
    tactic: StrategyTactic
    instruction: str = Field(
        min_length=1,
        max_length=500,
    )
    permitted_fact_ids: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_unique_fact_ids(
        self,
    ) -> "LegalStrategy":
        if len(self.permitted_fact_ids) != len(
            set(self.permitted_fact_ids)
        ):
            raise ValueError(
                "Permitted fact IDs must be unique."
            )

        return self

class StrategySpace(BaseModel):
    """The complete legal planning input for one response."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    suspect_id: str = Field(
        pattern=r"^suspect_[a-z0-9_]+$",
    )
    facts: tuple[StrategyFact, ...] = ()
    strategies: tuple[LegalStrategy, ...] = Field(
        min_length=1,
    )

    @model_validator(mode="after")
    def validate_strategy_space(
        self,
    ) -> "StrategySpace":
        fact_ids = [
            fact.id
            for fact in self.facts
        ]
        strategy_ids = [
            strategy.id
            for strategy in self.strategies
        ]

        if len(fact_ids) != len(set(fact_ids)):
            raise ValueError(
                "Strategy fact IDs must be unique."
            )

        if len(strategy_ids) != len(
            set(strategy_ids)
        ):
            raise ValueError(
                "Legal strategy IDs must be unique."
            )

        available_fact_ids = set(fact_ids)

        for strategy in self.strategies:
            unknown_fact_ids = (
                set(strategy.permitted_fact_ids)
                - available_fact_ids
            )

            if unknown_fact_ids:
                raise ValueError(
                    "Strategy references unavailable facts: "
                    f"{sorted(unknown_fact_ids)}."
                )

        return self


class StrategyProposal(BaseModel):
    """A non-authoritative strategy selected by the LLM."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    strategy_id: str = Field(
        pattern=r"^strategy_[a-z0-9_]+$",
    )
    fact_ids: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_unique_fact_ids(
        self,
    ) -> "StrategyProposal":
        if len(self.fact_ids) != len(
            set(self.fact_ids)
        ):
            raise ValueError(
                "Selected fact IDs must be unique."
            )

        return self

class SuspectPlan(BaseModel):
    """The validated application result."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    suspect_id: str = Field(
        pattern=r"^suspect_[a-z0-9_]+$",
    )
    strategy_id: str = Field(
        pattern=r"^strategy_[a-z0-9_]+$",
    )
    tactic: StrategyTactic
    selected_facts: tuple[StrategyFact, ...] = ()
    used_fallback: bool = False
