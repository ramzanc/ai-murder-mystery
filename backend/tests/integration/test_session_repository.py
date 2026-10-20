import asyncio

from app.infrastructure.database import (
    async_session_factory,
    engine,
)
from app.infrastructure.persistence.repositories import (
    SqlAlchemySessionRepository,
)
from tests.unit.repository_contract import (
    assert_session_repository_contract,
)


def test_sql_session_repository_contract() -> None:
    async def scenario() -> None:
        try:
            async with async_session_factory() as database:
                transaction = await database.begin()

                try:
                    repository = (
                        SqlAlchemySessionRepository(
                            database
                        )
                    )

                    await assert_session_repository_contract(
                        repository
                    )
                finally:
                    if transaction.is_active:
                        await transaction.rollback()
        finally:
            await engine.dispose()

    asyncio.run(scenario())
