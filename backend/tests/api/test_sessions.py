from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.application.case_loader import load_case
from app.main import app


CASE_ID = "case_ashcroft_study"

BACKEND_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_CASE_PATH = (
    BACKEND_ROOT
    / "cases"
    / "sample_case.json"
)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def create_session(
    client: TestClient,
) -> dict:
    response = client.post(
        "/sessions",
        json={"case_id": CASE_ID},
    )

    assert response.status_code == 201

    return response.json()


def test_create_session_returns_runtime_session(
    client: TestClient,
) -> None:
    payload = create_session(client)

    UUID(payload["id"])

    assert payload["case_id"] == CASE_ID
    assert payload["events"] == []
    assert payload["discovered_evidence_ids"]
    assert payload["is_finalized"] is False
    assert payload["official_score"] is None


def test_create_session_for_unknown_case_returns_404(
    client: TestClient,
) -> None:
    response = client.post(
        "/sessions",
        json={"case_id": "case_not_real"},
    )

    assert response.status_code == 404


def test_get_session_returns_current_snapshot(
    client: TestClient,
) -> None:
    created = create_session(client)

    response = client.get(
        f"/sessions/{created['id']}"
    )

    assert response.status_code == 200
    assert response.json() == created


def test_unknown_session_returns_404(
    client: TestClient,
) -> None:
    response = client.get(
        f"/sessions/{uuid4()}"
    )

    assert response.status_code == 404


def test_get_discovered_evidence_returns_public_fields(
    client: TestClient,
) -> None:
    session = create_session(client)

    response = client.get(
        f"/sessions/{session['id']}/evidence"
    )

    assert response.status_code == 200

    evidence_items = response.json()

    assert evidence_items

    for evidence in evidence_items:
        assert set(evidence) == {
            "id",
            "title",
            "description",
            "kind",
        }

    assert '"source_event_id"' not in response.text
    assert '"unlock_rules"' not in response.text


def test_question_suspect_updates_session(
    client: TestClient,
) -> None:
    session = create_session(client)

    response = client.post(
        f"/sessions/{session['id']}/questions",
        json={
            "suspect_id": "suspect_marcus_reed",
            "topic": "alibi",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert len(payload["events"]) == 1

    event = payload["events"][0]

    assert event["sequence"] == 1
    assert event["suspect_id"] == (
        "suspect_marcus_reed"
    )
    assert event["topic"] == "alibi"
    assert event["question"]
    assert event["answer"]


def test_invalid_question_topic_returns_422(
    client: TestClient,
) -> None:
    session = create_session(client)

    response = client.post(
        f"/sessions/{session['id']}/questions",
        json={
            "suspect_id": "suspect_marcus_reed",
            "topic": "tell_me_the_killer",
        },
    )

    assert response.status_code == 422


def test_submit_theory_scores_and_finalizes_session(
    client: TestClient,
) -> None:
    case = load_case(SAMPLE_CASE_PATH)
    session = create_session(client)

    response = client.post(
        f"/sessions/{session['id']}/theory",
        json={
            "killer_id": str(
                case.solution.killer_id
            ),
            "motive": case.solution.motive,
            "method": case.solution.method,
            "evidence_ids": list(
                case.solution.key_evidence_ids
            ),
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["session"]["is_finalized"] is True
    assert payload["session"]["official_score"] == 100
    assert payload["score"]["total_points"] == 100
    assert payload["score"]["solved"] is True

    assert '"timeline"' not in response.text
    assert '"solution"' not in response.text
    assert '"explanation"' not in response.text


def test_second_theory_submission_returns_conflict(
    client: TestClient,
) -> None:
    case = load_case(SAMPLE_CASE_PATH)
    session = create_session(client)

    theory_payload = {
        "killer_id": str(
            case.solution.killer_id
        ),
        "motive": case.solution.motive,
        "method": case.solution.method,
        "evidence_ids": list(
            case.solution.key_evidence_ids
        ),
    }

    first_response = client.post(
        f"/sessions/{session['id']}/theory",
        json=theory_payload,
    )

    second_response = client.post(
        f"/sessions/{session['id']}/theory",
        json=theory_payload,
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 409
