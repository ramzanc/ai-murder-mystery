from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AsyncOpenAI,
    InternalServerError,
    RateLimitError,
)
from pydantic import BaseModel

from app.application.ai_ports import (
    LLMError,
    LLMResponseError,
    LLMUnavailableError,
    StructuredOutputT,
)

_TRANSIENT_ERRORS = (
    APIConnectionError,
    APITimeoutError,
    InternalServerError,
    RateLimitError,
)

class OpenAIStructuredLLMClient:
    def __init__(
        self,
        *,
        model: str,
        timeout_seconds: float = 20.0,
        max_retries: int = 2,
        client: AsyncOpenAI | None = None,
    ) -> None:
        if not model.strip():
            raise ValueError(
                "Model name cannot be blank."
            )

        if timeout_seconds <= 0:
            raise ValueError(
                "Timeout must be greater than zero."
            )

        if max_retries < 0:
            raise ValueError(
                "Maximum retries cannot be negative."
            )

        self._model = model
        self._owns_client = client is None

        self._client = (
            client
            if client is not None
            else AsyncOpenAI(
                timeout=timeout_seconds,
                max_retries=max_retries,
            )
        )

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        output_type: type[StructuredOutputT],
    ) -> StructuredOutputT:
        if not system_prompt.strip():
            raise ValueError(
                "System prompt cannot be blank."
            )

        if not user_prompt.strip():
            raise ValueError(
                "User prompt cannot be blank."
            )

        try:
            response = await self._client.responses.parse(
                model=self._model,
                input=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                text_format=output_type,
            )
        except _TRANSIENT_ERRORS as error:
            raise LLMUnavailableError(
                "The language-model provider is unavailable."
            ) from error
        except APIError as error:
            raise LLMError(
                "The language-model provider rejected the request."
            ) from error

        parsed_output: BaseModel | None = (
            response.output_parsed
        )

        if parsed_output is None:
            raise LLMResponseError(
                "The language model returned no parsed output."
            )

        return output_type.model_validate(
            parsed_output
        )

    async def close(self) -> None:
        if self._owns_client:
            await self._client.close()
