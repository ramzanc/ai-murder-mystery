import pytest
from fastapi.testclient import TestClient

from app.main import app


CASE_ID = "case_ashcroft_study"


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_get_case_returns_public_case_data(
    client: TestClient,
) -> None:
    response = client.get(f"/cases/{CASE_ID}")

    assert response.status_code == 200

    payload = response.json()

    assert payload["id"] == CASE_ID
    assert payload["title"] == (
        "The Ashcroft Study Murder"
    )
    assert payload["difficulty"] == "medium"
    assert len(payload["suspects"]) == 4
    assert payload["initial_evidence"]


def test_public_case_has_only_expected_top_level_fields(
    client: TestClient,
) -> None:
    response = client.get(f"/cases/{CASE_ID}")

    assert response.status_code == 200

    assert set(response.json()) == {
        "id",
        "title",
        "difficulty",
        "dossier",
        "victim",
        "suspects",
        "initial_evidence",
        "accusation_options",
    }


def test_public_case_does_not_leak_hidden_truth(
    client: TestClient,
) -> None:
    response = client.get(f"/cases/{CASE_ID}")

    assert response.status_code == 200

    payload = response.json()
    serialized = response.text

    assert "timeline" not in payload
    assert "solution" not in payload

    assert '"knowledge"' not in serialized
    assert '"source_event_id"' not in serialized
    assert '"unlock_rules"' not in serialized
    assert '"killer_id"' not in serialized
    assert '"key_evidence_ids"' not in serialized
    assert '"explanation"' not in serialized


def test_unknown_case_returns_404(
    client: TestClient,
) -> None:
    response = client.get(
        "/cases/case_not_real"
    )

    assert response.status_code == 404
