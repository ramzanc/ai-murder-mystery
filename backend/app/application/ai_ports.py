from typing import Protocol, TypeVar

from pydantic import BaseModel

StructuredOutputT = TypeVar(
    "StructuredOutputT",
    bound=BaseModel,
)

class LLMError(RuntimeError):
    """Base error for hosted language-model operations."""


class LLMUnavailableError(LLMError):
    """Raised when a provider fails transiently."""


class LLMResponseError(LLMError):
    """Raised when a provider returns no usable output."""


class StructuredLLMClient(Protocol):
    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        output_type: type[StructuredOutputT],
    ) -> StructuredOutputT:
        """Generate and validate one structured proposal."""
        ...