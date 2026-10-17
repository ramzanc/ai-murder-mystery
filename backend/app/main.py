from fastapi import FastAPI

from app.api.routes.cases import router as cases_router
from app.api.routes.sessions import router as sessions_router


app = FastAPI(
    title="Daily Detective API",
    version="0.1.0",
)

app.include_router(cases_router)
app.include_router(sessions_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}