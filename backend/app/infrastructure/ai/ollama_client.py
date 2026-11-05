from httpx import TimeoutException
from ollama import AsyncClient, ResponseError
from pydantic import ValidationError

from app.application.ai_ports import (
    LLMError,
    LLMResponseError,
    LLMUnavailableError,
    StructuredOutputT,
)


class OllamaStructuredLLMClient:
    def __init__(
        self,
        *,
        model: str = "gemma4:12b",
        host: str = "http://127.0.0.1:11434",
        timeout_seconds: float = 180.0,
        num_ctx: int = 8192,
        client: AsyncClient | None = None,
    ) -> None:
        if not model.strip():
            raise ValueError(
                "Model name cannot be blank."
            )

        if not host.strip():
            raise ValueError(
                "Ollama host cannot be blank."
            )

        if timeout_seconds <= 0:
            raise ValueError(
                "Timeout must be greater than zero."
            )

        if num_ctx <= 0:
            raise ValueError(
                "Context size must be greater than zero."
            )

        self._model = model
        self._num_ctx = num_ctx
        self._owns_client = client is None

        self._client = (
            client
            if client is not None
            else AsyncClient(
                host=host,
                timeout=timeout_seconds,
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
            response = await self._client.chat(
                model=self._model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                format=output_type.model_json_schema(),
                options={
                    "temperature": 0.2,
                    "num_ctx": self._num_ctx,
                    "num_predict": 300,
                    "repeat_penalty": 1.15,
                    "repeat_last_n": 128,
                },
                think=False,
                keep_alive="10m",
            )
        except (ConnectionError, TimeoutException) as error:
            raise LLMUnavailableError(
                "The local Ollama server is unavailable."
            ) from error
        except ResponseError as error:
            if (
                error.status_code is not None
                and error.status_code >= 500
            ):
                raise LLMUnavailableError(
                    "The local Ollama server failed."
                ) from error

            raise LLMError(
                "Ollama rejected the model request."
            ) from error

        content = response.message.content

        if not content.strip():
            raise LLMResponseError(
                "Ollama returned no response content."
            )

        try:
            return output_type.model_validate_json(
                content
            )
        except ValidationError as error:
            raise LLMResponseError(
                "Ollama returned output that does not "
                "match the requested schema."
            ) from error

    async def close(self) -> None:
        if self._owns_client:
            await self._client.close()
