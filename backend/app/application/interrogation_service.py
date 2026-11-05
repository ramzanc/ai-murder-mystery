from time import perf_counter
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.application.intent_service import (
    INTENT_SYSTEM_PROMPT,
    IntentClassifier,
)
from app.application.investigation_service import (
    CaseNotFoundError,
    InvestigationUseCases,
)
from app.application.legal_strategies import (
    build_legal_strategy_space,
)
from app.application.ports import CaseFinder
from app.application.suspect_context import (
    build_suspect_context,
)
from app.application.suspect_dialogue import (
    DIALOGUE_PROMPT_VERSION,
    SuspectDialogue,
    SuspectDialogueGenerator,
)
from app.application.suspect_planner import (
    STRATEGY_SYSTEM_PROMPT,
    SuspectPlanner,
)
from app.domain.intent import ClassifiedIntent
from app.domain.strategy import SuspectPlan

INTENT_PROMPT_VERSION = "intent_classifier.v1"
STRATEGY_PROMPT_VERSION = "suspect_strategy.v1"


class InterrogationLatency(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    intent_ms: float = Field(ge=0.0)
    planning_ms: float = Field(ge=0.0)
    dialogue_ms: float = Field(ge=0.0)
    total_ms: float = Field(ge=0.0)

class InterrogationTrace(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    intent: str = Field(min_length=1)
    strategy_id: str = Field(min_length=1)
    tactic: str = Field(min_length=1)
    selected_fact_ids: tuple[str, ...]
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    intent_prompt_version: str = Field(min_length=1)
    strategy_prompt_version: str = Field(min_length=1)
    dialogue_prompt_version: str = Field(min_length=1)
    intent_used_fallback: bool
    strategy_used_fallback: bool
    dialogue_used_fallback: bool
    latency: InterrogationLatency

class InterrogationResult(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    session_id: UUID
    suspect_id: str = Field(
        pattern=r"^suspect_[a-z0-9_]+$",
    )
    question: str = Field(
        min_length=1,
        max_length=1000,
    )
    dialogue: str = Field(
        min_length=1,
        max_length=2000,
    )
    trace: InterrogationTrace

class InterrogationService:
    def __init__(
        self,
        *,
        investigation_use_cases: InvestigationUseCases,
        find_case: CaseFinder,
        intent_classifier: IntentClassifier,
        planner: SuspectPlanner,
        dialogue_generator: SuspectDialogueGenerator,
        provider: str,
        model: str,
    ) -> None:
        self._investigation_use_cases = (
            investigation_use_cases
        )
        self._find_case = find_case
        self._intent_classifier = intent_classifier
        self._planner = planner
        self._dialogue_generator = dialogue_generator
        self._provider = provider
        self._model = model

    async def interrogate(
        self,
        *,
        session_id: UUID,
        suspect_id: str,
        question: str,
        presented_evidence_ids: tuple[str, ...] = (),
    ) -> InterrogationResult:
        normalized_question = question.strip()

        if not normalized_question:
            raise ValueError(
                "Detective question cannot be blank."
            )

        total_started = perf_counter()

        record = (
            await self._investigation_use_cases.get_session(
                session_id
            )
        )

        case = self._find_case(record.session.case_id)

        if case is None:
            raise CaseNotFoundError(
                f"Case {record.session.case_id!r} was not found."
            )

        context = build_suspect_context(
            case=case,
            session=record.session,
            suspect_id=suspect_id,
            presented_evidence_ids=(
                presented_evidence_ids
            ),
        )

        intent_started = perf_counter()
        classified_intent = (
            await self._intent_classifier.classify(
                normalized_question
            )
        )
        intent_ms = _elapsed_ms(intent_started)

        strategy_space = build_legal_strategy_space(
            case=case,
            context=context,
            intent=classified_intent.intent,
        )

        planning_started = perf_counter()
        plan = await self._planner.plan(
            detective_question=normalized_question,
            strategy_space=strategy_space,
        )
        planning_ms = _elapsed_ms(planning_started)

        dialogue_started = perf_counter()
        dialogue = (
            await self._dialogue_generator.generate(
                context=context,
                detective_question=normalized_question,
                plan=plan,
            )
        )
        dialogue_ms = _elapsed_ms(dialogue_started)

        total_ms = _elapsed_ms(total_started)

        return InterrogationResult(
            session_id=session_id,
            suspect_id=suspect_id,
            question=normalized_question,
            dialogue=dialogue.text,
            trace=self._build_trace(
                intent=classified_intent,
                plan=plan,
                dialogue=dialogue,
                intent_ms=intent_ms,
                planning_ms=planning_ms,
                dialogue_ms=dialogue_ms,
                total_ms=total_ms,
            ),
        )

    def _build_trace(
        self,
        *,
        intent: ClassifiedIntent,
        plan: SuspectPlan,
        dialogue: SuspectDialogue,
        intent_ms: float,
        planning_ms: float,
        dialogue_ms: float,
        total_ms: float,
    ) -> InterrogationTrace:
        return InterrogationTrace(
            intent=intent.intent.value,
            strategy_id=plan.strategy_id,
            tactic=plan.tactic.value,
            selected_fact_ids=tuple(
                fact.id
                for fact in plan.selected_facts
            ),
            provider=self._provider,
            model=self._model,
            intent_prompt_version=(
                INTENT_PROMPT_VERSION
            ),
            strategy_prompt_version=(
                STRATEGY_PROMPT_VERSION
            ),
            dialogue_prompt_version=(
                DIALOGUE_PROMPT_VERSION
            ),
            intent_used_fallback=(
                intent.used_fallback
            ),
            strategy_used_fallback=(
                plan.used_fallback
            ),
            dialogue_used_fallback=(
                dialogue.used_fallback
            ),
            latency=InterrogationLatency(
                intent_ms=intent_ms,
                planning_ms=planning_ms,
                dialogue_ms=dialogue_ms,
                total_ms=total_ms,
            ),
        )

def _elapsed_ms(started: float) -> float:
    return round(
        (perf_counter() - started) * 1000,
        2,
    )