from pathlib import Path

import pytest

from app.application.case_loader import load_case
from app.application.investigation_service import (
    ask_question,
    start_session,
)
from app.application.suspect_context import (
    ContextSuspectNotFoundError,
    EvidenceNotAvailableError,
    build_suspect_context,
)
from app.domain.investigation import QuestionTopic
from app.domain.knowledge import (
    Belief,
    Observation,
    SuspectKnowledge,
)
from app.infrastructure.ai.prompts import (
    build_suspect_prompt,
)


CASE_PATH = (
    Path(__file__).parents[2]
    / "cases"
    / "sample_case.json"
)

MARCUS_ID = "suspect_marcus_reed"
MAYA_ID = "suspect_maya_sen"

MAYA_PRIVATE_FACT = (
    "Iris told Maya that Adrian planned to cancel "
    "the development contract."
)


@pytest.fixture
def case():
    loaded_case = load_case(CASE_PATH)

    updated_suspects = tuple(
        suspect.model_copy(
            update={
                "knowledge": SuspectKnowledge(
                    observations=(
                        Observation(
                            id="observation_maya_private_call",
                            source_event_id=(
                                "timeline_event_maya_terrace"
                            ),
                            perceived_description=(
                                MAYA_PRIVATE_FACT
                            ),
                            confidence=0.95,
                        ),
                    ),
                    beliefs=(
                        Belief(
                            id="belief_maya_contract",
                            about_event_id=(
                                "timeline_event_maya_terrace"
                            ),
                            statement=(
                                "Adrian was reconsidering "
                                "the contract."
                            ),
                            confidence=0.80,
                            based_on_observation_ids=(
                                "observation_maya_private_call",
                            ),
                        ),
                    ),
                )
            }
        )
        if str(suspect.id) == MAYA_ID
        else suspect
        for suspect in loaded_case.suspects
    )

    return loaded_case.model_copy(
        update={
            "suspects": updated_suspects,
        }
    )


def test_context_contains_only_target_suspect_chat(
    case,
) -> None:
    session = start_session(case)

    session = ask_question(
        case=case,
        session=session,
        suspect_id=MAYA_ID,
        topic=QuestionTopic.ALIBI,
    )
    session = ask_question(
        case=case,
        session=session,
        suspect_id=MARCUS_ID,
        topic=QuestionTopic.SECRET,
    )

    context = build_suspect_context(
        case=case,
        session=session,
        suspect_id=MARCUS_ID,
    )

    assert len(context.own_chat) == 1
    assert context.own_chat[0].sequence == 2
    assert (
        context.own_chat[0].question
        == "Is there anything important you're hiding from us?"
    )


def test_context_contains_only_presented_evidence(
    case,
) -> None:
    session = start_session(case)

    context = build_suspect_context(
        case=case,
        session=session,
        suspect_id=MARCUS_ID,
        presented_evidence_ids=(
            "evidence_cracked_watch",
        ),
    )

    assert [
        evidence.id
        for evidence in context.presented_evidence
    ] == ["evidence_cracked_watch"]


def test_context_excludes_private_and_canonical_truth(
    case,
) -> None:
    session = start_session(case)

    context = build_suspect_context(
        case=case,
        session=session,
        suspect_id=MARCUS_ID,
        presented_evidence_ids=(
            "evidence_cracked_watch",
        ),
    )

    serialized_context = context.model_dump_json()

    assert MAYA_PRIVATE_FACT not in serialized_context
    assert case.solution.motive not in serialized_context
    assert case.solution.method not in serialized_context
    assert case.solution.explanation not in serialized_context
    assert '"solution"' not in serialized_context
    assert '"killer_id"' not in serialized_context


def test_context_construction_is_deterministic(
    case,
) -> None:
    session = start_session(case)

    first = build_suspect_context(
        case=case,
        session=session,
        suspect_id=MARCUS_ID,
        presented_evidence_ids=(
            "evidence_torn_note",
            "evidence_cracked_watch",
        ),
    )
    second = build_suspect_context(
        case=case,
        session=session,
        suspect_id=MARCUS_ID,
        presented_evidence_ids=(
            "evidence_cracked_watch",
            "evidence_torn_note",
        ),
    )

    assert first == second
    assert (
        first.model_dump_json(indent=2)
        == second.model_dump_json(indent=2)
    )
    assert [
        evidence.id
        for evidence in first.presented_evidence
    ] == [
        "evidence_cracked_watch",
        "evidence_torn_note",
    ]


def test_prompt_does_not_reintroduce_forbidden_truth(
    case,
) -> None:
    session = start_session(case)

    context = build_suspect_context(
        case=case,
        session=session,
        suspect_id=MARCUS_ID,
    )

    prompt = build_suspect_prompt(
        context=context,
        detective_question=(
            "What do you know about Adrian's plans?"
        ),
    )

    combined_prompt = (
        prompt.system_prompt
        + "\n"
        + prompt.user_prompt
    )

    assert MAYA_PRIVATE_FACT not in combined_prompt
    assert case.solution.explanation not in combined_prompt
    assert "<suspect_context>" in prompt.user_prompt
    assert "<detective_question>" in prompt.user_prompt


def test_unknown_suspect_is_rejected(case) -> None:
    session = start_session(case)

    with pytest.raises(
        ContextSuspectNotFoundError,
        match="Unknown suspect ID",
    ):
        build_suspect_context(
            case=case,
            session=session,
            suspect_id="suspect_unknown",
        )


def test_undiscovered_evidence_is_rejected(
    case,
) -> None:
    session = start_session(case).model_copy(
        update={
            "discovered_evidence_ids": (),
        }
    )

    with pytest.raises(
        EvidenceNotAvailableError,
        match="has not been discovered",
    ):
        build_suspect_context(
            case=case,
            session=session,
            suspect_id=MARCUS_ID,
            presented_evidence_ids=(
                "evidence_cracked_watch",
            ),
        )