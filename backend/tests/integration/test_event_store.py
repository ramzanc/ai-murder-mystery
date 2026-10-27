import asyncio
from pathlib import Path
from uuid import uuid4

import pytest

from app.application.case_loader import load_case
from app.application.event_store import (
    EventStore,
    OptimisticConcurrencyError,
)
from app.application.investigation_service import (
    ask_question,
    start_session,
    submit_final_theory,
)
from app.domain.events import (
    QuestionAsked,
    SessionStarted,
    TheorySubmitted,
)
from app.domain.investigation import QuestionTopic
from app.domain.theory import Theory
from app.infrastructure.database import (
    async_session_factory,
    engine,
)
from app.infrastructure.persistence.event_repository import (
    SqlAlchemySessionEventRepository,
)


BACKEND_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_CASE_PATH = (
    BACKEND_ROOT
    / "cases"
    / "sample_case.json"
)


def test_postgresql_event_store_contract() -> None:
    async def scenario() -> None:
        case = load_case(SAMPLE_CASE_PATH)
        session_id = uuid4()

        initial_session = start_session(case)

        after_question = ask_question(
            case=case,
            session=initial_session,
            suspect_id=str(case.suspects[0].id),
            topic=QuestionTopic.ALIBI,
        )

        theory = Theory(
            killer_id=case.solution.killer_id,
            motive=case.solution.motive,
            method=case.solution.method,
            evidence_ids=(
                case.solution.key_evidence_ids
            ),
        )

        finalized_session, _ = submit_final_theory(
            case=case,
            session=after_question,
            theory=theory,
        )

        assert (
            finalized_session.final_submission
            is not None
        )

        try:
            async with async_session_factory() as database:
                transaction = await database.begin()

                try:
                    repository = (
                        SqlAlchemySessionEventRepository(
                            database
                        )
                    )
                    event_store = EventStore(repository)

                    first = await event_store.append(
                        session_id=session_id,
                        expected_version=0,
                        idempotency_key="start-session",
                        payload=SessionStarted(
                            case_id=initial_session.case_id,
                            discovered_evidence_ids=(
                                initial_session
                                .discovered_evidence_ids
                            ),
                        ),
                    )

                    duplicate = await event_store.append(
                        session_id=session_id,
                        expected_version=999,
                        idempotency_key="start-session",
                        payload=SessionStarted(
                            case_id="case_ignored_retry",
                        ),
                    )

                    assert duplicate == first
                    assert duplicate.sequence == 1

                    second = await event_store.append(
                        session_id=session_id,
                        expected_version=1,
                        idempotency_key="ask-alibi",
                        payload=QuestionAsked(
                            question=(
                                after_question.events[-1]
                            ),
                        ),
                    )

                    assert second.sequence == 2

                    with pytest.raises(
                        OptimisticConcurrencyError,
                        match="expected 1",
                    ):
                        await event_store.append(
                            session_id=session_id,
                            expected_version=1,
                            idempotency_key=(
                                "stale-question"
                            ),
                            payload=QuestionAsked(
                                question=(
                                    after_question.events[-1]
                                ),
                            ),
                        )

                    third = await event_store.append(
                        session_id=session_id,
                        expected_version=2,
                        idempotency_key="submit-theory",
                        payload=TheorySubmitted(
                            submission=(
                                finalized_session
                                .final_submission
                            ),
                        ),
                    )

                    assert third.sequence == 3

                    stored_events = (
                        await event_store.load(session_id)
                    )

                    assert [
                        event.sequence
                        for event in stored_events
                    ] == [1, 2, 3]

                    rebuilt_session = (
                        await event_store.rebuild_session(
                            session_id
                        )
                    )

                    assert rebuilt_session == (
                        finalized_session
                    )
                finally:
                    if transaction.is_active:
                        await transaction.rollback()
        finally:
            await engine.dispose()

    asyncio.run(scenario())