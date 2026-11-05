import asyncio
from pathlib import Path
from uuid import uuid4

from app.application.ai_ports import StructuredOutputT
from app.application.case_loader import load_case
from app.application.intent_service import IntentClassifier
from app.application.interrogation_service import (
    InterrogationService,
)
from app.application.investigation_service import (
    InvestigationUseCases,
    start_session,
)
from app.application.legal_strategies import (
    build_legal_strategy_space,
)
from app.application.ports import SessionRecord
from app.application.suspect_dialogue import (
    DialogueProposal,
    SuspectDialogueGenerator,
)
from app.application.suspect_planner import SuspectPlanner
from app.domain.intent import (
    IntentEntities,
    IntentProposal,
    SemanticIntent,
)
from app.domain.strategy import StrategyProposal
from tests.unit.fakes import (
    FakeSessionRepository,
    FakeUnitOfWork,
)


CASE_PATH = (
    Path(__file__).parents[2]
    / "cases"
    / "sample_case.json"
)

SUSPECT_ID = "suspect_marcus_reed"


class ScriptedInterrogationClient:
    def __init__(self) -> None:
        self.calls: list[type[object]] = []

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        output_type: type[StructuredOutputT],
    ) -> StructuredOutputT:
        assert system_prompt
        assert user_prompt

        self.calls.append(output_type)

        if output_type is IntentProposal:
            proposal = IntentProposal(
                intent=SemanticIntent.DISCUSS_EVIDENCE,
                confidence=0.98,
                entities=IntentEntities(
                    evidence_mentions=(
                        "cracked watch",
                    ),
                ),
            )
            return output_type.model_validate(proposal)

        if output_type is StrategyProposal:
            assert '"solution"' not in user_prompt
            assert '"killer_id"' not in user_prompt

            proposal = StrategyProposal(
                strategy_id="strategy_redirect",
                fact_ids=(
                    "fact_evidence_cracked_watch",
                ),
            )
            return output_type.model_validate(proposal)

        if output_type is DialogueProposal:
            assert "cracked" in user_prompt.lower()
            assert "validated_response_plan" in user_prompt

            proposal = DialogueProposal(
                dialogue=(
                    "A cracked watch tells you when its "
                    "mechanism stopped, not who caused it."
                ),
            )
            return output_type.model_validate(proposal)

        raise AssertionError(
            f"Unexpected output type: {output_type}"
        )


def test_free_text_question_reaches_validated_dialogue() -> None:
    async def scenario() -> None:
        case = load_case(CASE_PATH)
        session_id = uuid4()

        record = SessionRecord(
            id=session_id,
            session=start_session(case),
        )

        repository = FakeSessionRepository(
            records={
                session_id: record,
            }
        )
        unit_of_work = FakeUnitOfWork(repository)

        client = ScriptedInterrogationClient()

        use_cases = InvestigationUseCases(
            unit_of_work=unit_of_work,
            find_case=lambda case_id: (
                case
                if case_id == str(case.id)
                else None
            ),
        )

        service = InterrogationService(
            investigation_use_cases=use_cases,
            find_case=lambda case_id: (
                case
                if case_id == str(case.id)
                else None
            ),
            intent_classifier=IntentClassifier(
                llm_client=client,
            ),
            planner=SuspectPlanner(
                llm_client=client,
            ),
            dialogue_generator=(
                SuspectDialogueGenerator(
                    llm_client=client,
                )
            ),
            provider="test",
            model="scripted-model",
        )

        before = repository.records[
            session_id
        ].session

        result = await service.interrogate(
            session_id=session_id,
            suspect_id=SUSPECT_ID,
            question=(
                "Your cracked watch stopped at 10:12. "
                "What does that prove?"
            ),
            presented_evidence_ids=(
                "evidence_cracked_watch",
            ),
        )

        after = repository.records[
            session_id
        ].session

        assert result.session_id == session_id
        assert result.suspect_id == SUSPECT_ID
        assert result.dialogue == (
            "A cracked watch tells you when its "
            "mechanism stopped, not who caused it."
        )

        assert result.trace.intent == (
            "discuss_evidence"
        )
        assert result.trace.strategy_id == (
            "strategy_redirect"
        )
        assert result.trace.tactic == "redirect"
        assert result.trace.selected_fact_ids == (
            "fact_evidence_cracked_watch",
        )
        assert result.trace.provider == "test"
        assert result.trace.model == "scripted-model"

        assert result.trace.intent_prompt_version == (
            "intent_classifier.v1"
        )
        assert result.trace.strategy_prompt_version == (
            "suspect_strategy.v1"
        )
        assert result.trace.dialogue_prompt_version == (
            "suspect_dialogue.v1"
        )

        assert result.trace.latency.intent_ms >= 0
        assert result.trace.latency.planning_ms >= 0
        assert result.trace.latency.dialogue_ms >= 0
        assert result.trace.latency.total_ms >= 0

        assert before == after
        assert unit_of_work.enter_count == 1
        assert unit_of_work.commit_count == 1

        assert client.calls == [
            IntentProposal,
            StrategyProposal,
            DialogueProposal,
        ]

    asyncio.run(scenario())