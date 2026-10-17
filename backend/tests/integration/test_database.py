from fastapi.testclient import TestClient

from app.main import app


CASE_ID = "case_ashcroft_study"


def test_database_health_check_passes() -> None:
    with TestClient(app) as client:
        response = client.get(
            "/health/database"
        )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "database": "reachable",
    }


def test_session_persists_across_app_restart() -> None:
    with TestClient(app) as first_process:
        create_response = first_process.post(
            "/sessions",
            json={
                "case_id": CASE_ID,
            },
        )

        assert create_response.status_code == 201
        created = create_response.json()

    # Leaving the first context shuts down the application
    # and disposes its database connection pool.

    with TestClient(app) as restarted_process:
        get_response = restarted_process.get(
            f"/sessions/{created['id']}"
        )

    assert get_response.status_code == 200
    assert get_response.json() == created