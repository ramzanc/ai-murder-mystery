from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status

from app.api.routes.cases import router as cases_router
from app.api.routes.sessions import router as sessions_router
from app.infrastructure.database import (
    database_is_available,
    engine,
)


@asynccontextmanager
async def lifespan(
    _: FastAPI,
) -> AsyncIterator[None]:
    yield
    await engine.dispose()


app = FastAPI(
    title="Daily Detective API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(cases_router)
app.include_router(sessions_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/database")
async def database_health() -> dict[str, str]:
    if not await database_is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable.",
        )

    return {
        "status": "ok",
        "database": "reachable",
    }