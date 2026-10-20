import asyncio
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from app.application.case_loader import load_case
from app.application.investigation_service import (
    InvestigationUseCases,
    InvalidSuspectError,
    SessionNotFoundError,
    start_session,
)
from app.application.ports import SessionRecord
from app.domain.case import CaseManifest
from app.domain.investigation import QuestionTopic
from app.domain.theory import Theory
from tests.unit.fakes import (
    FakeSessionRepository,
    FakeUnitOfWork,
)


BACKEND_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_CASE_PATH = (
    BACKEND_ROOT
    / "cases"
    / "sample_case.json"
)


@pytest.fixture
def case() -> CaseManifest:
    return load_case(SAMPLE_CASE_PATH)


def build_use_cases(
    case: CaseManifest,
    records: dict[UUID, SessionRecord] | None = None,
) -> tuple[
    InvestigationUseCases,
    FakeSessionRepository,
    FakeUnitOfWork,
]:
    repository = FakeSessionRepository(records)
    unit_of_work = FakeUnitOfWork(repository)

    cases: dict[str, CaseManifest] = {
        str(case.id): case,
    }

    def find_case(
        case_id: str,
    ) -> CaseManifest | None:
        return cases.get(case_id)

    use_cases = InvestigationUseCases(
        unit_of_work=unit_of_work,
        find_case=find_case,
    )

    return use_cases, repository, unit_of_work


def test_create_session_uses_one_transaction(
    case,
) -> None:
    async def scenario() -> None:
        use_cases, repository, unit_of_work = (
            build_use_cases(case)
        )

        record = await use_cases.create_session(
            str(case.id)
        )

        assert repository.records[record.id] == record
        assert record.session.case_id == str(case.id)

        assert unit_of_work.enter_count == 1
        assert unit_of_work.commit_count == 1
        assert unit_of_work.rollback_count == 0

    asyncio.run(scenario())


def test_get_session_from_fake_repository(
    case,
) -> None:
    async def scenario() -> None:
        use_cases, _, unit_of_work = (
            build_use_cases(case)
        )

        created = await use_cases.create_session(
            str(case.id)
        )

        loaded = await use_cases.get_session(
            created.id
        )

        assert loaded == created
        assert unit_of_work.enter_count == 2
        assert unit_of_work.commit_count == 2

    asyncio.run(scenario())


def test_question_updates_fake_repository(
    case,
) -> None:
    async def scenario() -> None:
        session_id = uuid4()

        initial_record = SessionRecord(
            id=session_id,
            session=start_session(case),
        )

        use_cases, repository, unit_of_work = (
            build_use_cases(
                case,
                records={
                    session_id: initial_record,
                },
            )
        )

        updated = await use_cases.question_suspect(
            session_id=session_id,
            suspect_id=str(case.suspects[0].id),
            topic=QuestionTopic.ALIBI,
        )

        assert len(updated.session.events) == 1
        assert repository.records[session_id] == updated

        assert unit_of_work.enter_count == 1
        assert unit_of_work.commit_count == 1

    asyncio.run(scenario())


def test_invalid_operation_rolls_back(
    case,
) -> None:
    async def scenario() -> None:
        session_id = uuid4()

        initial_record = SessionRecord(
            id=session_id,
            session=start_session(case),
        )

        use_cases, repository, unit_of_work = (
            build_use_cases(
                case,
                records={
                    session_id: initial_record,
                },
            )
        )

        with pytest.raises(InvalidSuspectError):
            await use_cases.question_suspect(
                session_id=session_id,
                suspect_id="suspect_not_real",
                topic=QuestionTopic.ALIBI,
            )

        assert repository.records[session_id] == (
            initial_record
        )
        assert unit_of_work.commit_count == 0
        assert unit_of_work.rollback_count == 1

    asyncio.run(scenario())


def test_missing_session_rolls_back(
    case,
) -> None:
    async def scenario() -> None:
        use_cases, _, unit_of_work = (
            build_use_cases(case)
        )

        with pytest.raises(SessionNotFoundError):
            await use_cases.get_session(uuid4())

        assert unit_of_work.commit_count == 0
        assert unit_of_work.rollback_count == 1

    asyncio.run(scenario())


def test_submit_theory_persists_finalized_session(
    case,
) -> None:
    async def scenario() -> None:
        use_cases, repository, unit_of_work = (
            build_use_cases(case)
        )

        created = await use_cases.create_session(
            str(case.id)
        )

        theory = Theory(
            killer_id=case.solution.killer_id,
            motive=case.solution.motive,
            method=case.solution.method,
            evidence_ids=(
                case.solution.key_evidence_ids
            ),
        )

        finalized, score = await use_cases.submit_theory(
            session_id=created.id,
            theory=theory,
        )

        assert finalized.session.is_finalized
        assert score.total_points == 100
        assert repository.records[created.id] == (
            finalized
        )

        assert unit_of_work.enter_count == 2
        assert unit_of_work.commit_count == 2

    asyncio.run(scenario())
