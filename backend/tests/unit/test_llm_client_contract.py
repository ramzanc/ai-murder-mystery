import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.ai_ports import (
    LLMResponseError,
    StructuredLLMClient,
)
from app.infrastructure.ai.llm_client import (
    OpenAIStructuredLLMClient,
)
from app.infrastructure.ai.schemas import (
    ClueAssessmentProposal,
    ClueRelevance,
)


SYSTEM_PROMPT = (
    "Assess the supplied clue. "
    "Return an advisory proposal only. "
    "Do not claim that your assessment is canonical truth."
)

USER_PROMPT = (
    "A receipt is timestamped 9:14 PM, "
    "close to the estimated murder window."
)


def accepts_structured_client(
    client: StructuredLLMClient,
) -> StructuredLLMClient:
    return client


def test_client_returns_parsed_pydantic_output() -> None:
    async def scenario() -> None:
        expected = ClueAssessmentProposal(
            summary=(
                "The receipt was issued near "
                "the estimated murder window."
            ),
            proposed_relevance=ClueRelevance.HIGH,
            rationale=(
                "Its timestamp may help establish "
                "a person's location."
            ),
        )

        sdk = MagicMock()
        sdk.responses.parse = AsyncMock(
            return_value=SimpleNamespace(
                output_parsed=expected,
            ),
        )

        client = OpenAIStructuredLLMClient(
            model="test-model",
            client=sdk,
        )

        accepts_structured_client(client)

        result = await client.generate_structured(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=USER_PROMPT,
            output_type=ClueAssessmentProposal,
        )

        assert result == expected

        sdk.responses.parse.assert_awaited_once_with(
            model="test-model",
            input=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": USER_PROMPT,
                },
            ],
            text_format=ClueAssessmentProposal,
        )

    asyncio.run(scenario())


def test_client_rejects_missing_parsed_output() -> None:
    async def scenario() -> None:
        sdk = MagicMock()
        sdk.responses.parse = AsyncMock(
            return_value=SimpleNamespace(
                output_parsed=None,
            ),
        )

        client = OpenAIStructuredLLMClient(
            model="test-model",
            client=sdk,
        )

        with pytest.raises(
            LLMResponseError,
            match="no parsed output",
        ):
            await client.generate_structured(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=USER_PROMPT,
                output_type=ClueAssessmentProposal,
            )

    asyncio.run(scenario())


@pytest.mark.parametrize(
    ("argument", "value", "message"),
    [
        ("model", "   ", "Model name cannot be blank"),
        (
            "timeout_seconds",
            0,
            "Timeout must be greater than zero",
        ),
        (
            "max_retries",
            -1,
            "Maximum retries cannot be negative",
        ),
    ],
)
def test_client_rejects_invalid_configuration(
    argument: str,
    value: object,
    message: str,
) -> None:
    arguments: dict[str, object] = {
        "model": "test-model",
        "timeout_seconds": 20.0,
        "max_retries": 2,
        "client": MagicMock(),
    }

    arguments[argument] = value

    with pytest.raises(
        ValueError,
        match=message,
    ):
        OpenAIStructuredLLMClient(**arguments)