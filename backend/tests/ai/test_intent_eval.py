import asyncio
import json
from pathlib import Path

import pytest

from app.application.ai_ports import (
    LLMUnavailableError,
    StructuredOutputT,
)
from app.application.intent_service import (
    IntentClassifier,
)
from app.domain.intent import (
    IntentEntities,
    IntentProposal,
    SemanticIntent,
)


EVAL_PATH = (
    Path(__file__).parents[2]
    / "evals"
    / "intent_cases.jsonl"
)


def load_golden_cases() -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in EVAL_PATH.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]


def read_string_tuple(
    case: dict[str, object],
    field: str,
) -> tuple[str, ...]:
    value = case[field]

    if not isinstance(value, list) or not all(
        isinstance(item, str)
        for item in value
    ):
        raise ValueError(
            f"Golden case field {field!r} must be a list of strings."
        )

    return tuple(value)


class GoldenIntentClient:
    def __init__(
        self,
        cases: list[dict[str, object]],
    ) -> None:
        self._cases_by_message = {
            str(case["message"]): case
            for case in cases
        }

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        output_type: type[StructuredOutputT],
    ) -> StructuredOutputT:
        assert system_prompt
        assert output_type is IntentProposal

        case = self._cases_by_message[user_prompt]
        expected_intent = SemanticIntent(
            str(case["expected_intent"])
        )

        confidence = (
            0.95
            if expected_intent is not SemanticIntent.UNKNOWN
            else 0.40
        )

        proposal = IntentProposal(
            intent=expected_intent,
            confidence=confidence,
            entities=IntentEntities(
                suspect_mentions=read_string_tuple(
                    case,
                    "suspect_mentions",
                ),
                time_references=read_string_tuple(
                    case,
                    "time_references",
                ),
                evidence_mentions=read_string_tuple(
                    case,
                    "evidence_mentions",
                ),
            ),
        )

        return output_type.model_validate(proposal)


class FailingIntentClient:
    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        output_type: type[StructuredOutputT],
    ) -> StructuredOutputT:
        raise LLMUnavailableError(
            "The model is unavailable."
        )


def test_golden_intent_cases() -> None:
    async def scenario() -> None:
        cases = load_golden_cases()
        classifier = IntentClassifier(
            llm_client=GoldenIntentClient(cases),
        )

        for case in cases:
            result = await classifier.classify(
                str(case["message"])
            )

            assert result.intent is SemanticIntent(
                str(case["expected_intent"])
            )

            if result.intent is SemanticIntent.UNKNOWN:
                assert result.used_fallback is True
                assert result.entities == IntentEntities()
            else:
                assert result.used_fallback is False
                assert result.entities.suspect_mentions == read_string_tuple(
                    case,
                    "suspect_mentions",
                )
                assert result.entities.time_references == read_string_tuple(
                    case,
                    "time_references",
                )
                assert result.entities.evidence_mentions == read_string_tuple(
                    case,
                    "evidence_mentions",
                )

    asyncio.run(scenario())


def test_alibi_paraphrases_have_same_intent() -> None:
    async def scenario() -> None:
        cases = load_golden_cases()
        classifier = IntentClassifier(
            llm_client=GoldenIntentClient(cases),
        )

        casual = await classifier.classify(
            "Where were you around ten?"
        )
        direct = await classifier.classify(
            "What's your alibi for 10pm?"
        )

        assert casual.intent is SemanticIntent.ASK_ALIBI
        assert direct.intent is SemanticIntent.ASK_ALIBI

    asyncio.run(scenario())


def test_low_confidence_proposal_falls_back() -> None:
    class UncertainClient:
        async def generate_structured(
            self,
            *,
            system_prompt: str,
            user_prompt: str,
            output_type: type[StructuredOutputT],
        ) -> StructuredOutputT:
            proposal = IntentProposal(
                intent=SemanticIntent.ASK_ALIBI,
                confidence=0.69,
                entities=IntentEntities(
                    time_references=("around ten",),
                ),
            )

            return output_type.model_validate(proposal)

    async def scenario() -> None:
        classifier = IntentClassifier(
            llm_client=UncertainClient(),
            confidence_threshold=0.70,
        )

        result = await classifier.classify(
            "Maybe something about where you were?"
        )

        assert result.intent is SemanticIntent.UNKNOWN
        assert result.confidence == 0.69
        assert result.entities == IntentEntities()
        assert result.used_fallback is True

    asyncio.run(scenario())


def test_provider_failure_falls_back() -> None:
    async def scenario() -> None:
        classifier = IntentClassifier(
            llm_client=FailingIntentClient(),
        )

        result = await classifier.classify(
            "Where were you at ten?"
        )

        assert result.intent is SemanticIntent.UNKNOWN
        assert result.confidence == 0.0
        assert result.used_fallback is True

    asyncio.run(scenario())


def test_blank_message_falls_back_without_calling_model() -> None:
    class UnexpectedClient:
        async def generate_structured(
            self,
            *,
            system_prompt: str,
            user_prompt: str,
            output_type: type[StructuredOutputT],
        ) -> StructuredOutputT:
            pytest.fail(
                "The LLM should not receive a blank message."
            )

    async def scenario() -> None:
        classifier = IntentClassifier(
            llm_client=UnexpectedClient(),
        )

        result = await classifier.classify("   ")

        assert result.intent is SemanticIntent.UNKNOWN
        assert result.used_fallback is True

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "threshold",
    [-0.01, 1.01],
)
def test_invalid_confidence_threshold_is_rejected(
    threshold: float,
) -> None:
    with pytest.raises(
        ValueError,
        match="between 0.0 and 1.0",
    ):
        IntentClassifier(
            llm_client=FailingIntentClient(),
            confidence_threshold=threshold,
        )
