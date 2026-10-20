import asyncio

from tests.unit.fakes import FakeSessionRepository
from tests.unit.repository_contract import (
    assert_session_repository_contract,
)


def test_fake_session_repository_contract() -> None:
    asyncio.run(
        assert_session_repository_contract(
            FakeSessionRepository()
        )
    )