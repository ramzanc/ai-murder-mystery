from uuid import uuid4

from app.application.ports import (
    SessionRecord,
    SessionRepository,
)
from app.domain.investigation import InvestigationSession


async def assert_session_repository_contract(
    repository: SessionRepository,
) -> None:
    session_id = uuid4()

    initial_record = SessionRecord(
        id=session_id,
        session=InvestigationSession(
            case_id="case_repository_contract",
        ),
    )

    await repository.add(initial_record)

    loaded = await repository.get(session_id)

    assert loaded == initial_record

    updated_record = SessionRecord(
        id=session_id,
        session=initial_record.session.model_copy(
            update={
                "discovered_evidence_ids": (
                    "evidence_contract",
                ),
            }
        ),
    )

    await repository.replace(updated_record)

    reloaded = await repository.get(session_id)

    assert reloaded == updated_record