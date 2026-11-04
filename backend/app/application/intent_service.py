from app.application.ai_ports import (
    LLMError,
    StructuredLLMClient,
)
from app.domain.intent import (
    ClassifiedIntent,
    IntentEntities,
    IntentProposal,
    SemanticIntent,
)

INTENT_SYSTEM_PROMPT = """
You classify detective questions for a murder-mystery game.

Return exactly one structured intent proposal.

Available intents:
- ask_alibi: asks where someone was or who can confirm it
- probe_secret: asks what someone is hiding or withholding
- ask_timeline: asks when an event happened or about event ordering
- discuss_evidence: asks about, presents, or challenges physical evidence
- unknown: the message is unrelated, ambiguous, or cannot be classified safely

Extract entity text only when it is explicitly present:
- suspect_mentions: names or descriptions of people
- time_references: times, dates, or relative time phrases
- evidence_mentions: clues or physical evidence mentioned by the detective

Do not invent entities.
Confidence must be between 0.0 and 1.0.
Classification is advisory and cannot change game state.
""".strip()

class IntentClassifier:
    def __init__(
        self,
        *,
        llm_client: StructuredLLMClient,
        confidence_threshold: float = 0.70,
    ) -> None:
        if not 0.0 <= confidence_threshold <= 1.0:
            raise ValueError(
                "Confidence threshold must be between 0.0 and 1.0."
            )

        self._llm_client = llm_client
        self._confidence_threshold = confidence_threshold

    async def classify(
        self,
        detective_message: str,
    ) -> ClassifiedIntent:
        normalized_message = detective_message.strip()

        if not normalized_message:
            return self._fallback(confidence=0.0)

        try:
            proposal = (
                await self._llm_client.generate_structured(
                    system_prompt=INTENT_SYSTEM_PROMPT,
                    user_prompt=normalized_message,
                    output_type=IntentProposal,
                )
            )
        except LLMError:
            return self._fallback(confidence=0.0)

        if (
            proposal.intent is SemanticIntent.UNKNOWN
            or proposal.confidence < self._confidence_threshold
        ):
            return self._fallback(
                confidence=proposal.confidence,
            )

        return ClassifiedIntent(
            intent=proposal.intent,
            confidence=proposal.confidence,
            entities=proposal.entities,
            used_fallback=False,
        )

    @staticmethod
    def _fallback(
        *,
        confidence: float,
    ) -> ClassifiedIntent:
        return ClassifiedIntent(
            intent=SemanticIntent.UNKNOWN,
            confidence=confidence,
            entities=IntentEntities(),
            used_fallback=True,
        )