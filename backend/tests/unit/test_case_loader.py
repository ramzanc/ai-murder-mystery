import json

import pytest

from app.application.case_loader import (
    CaseFileNotFoundError,
    CaseJsonError,
    CaseSchemaError,
    load_case,
)
from app.domain.case import CaseManifest


def valid_case_payload() -> dict:
    return {
        "schema_version": 1,
        "id": "case_loader_test",
        "title": "Loader Test Case",
        "difficulty": "easy",
        "dossier": {
            "summary": "A victim was found in a locked office.",
            "location": "Westbridge Office",
            "incident_time": "9:30 PM",
        },
        "victim": {
            "id": "victim_alex_hart",
            "name": "Alex Hart",
            "age": 45,
            "public_profile": (
                "The director of a small technology company."
            ),
        },
        "suspects": [
            {
                "id": "suspect_one",
                "name": "Suspect One",
                "age": 30,
                "occupation": "Engineer",
                "relationship_to_victim": "Colleague",
                "public_profile": (
                    "Worked closely with the victim."
                ),
            },
            {
                "id": "suspect_two",
                "name": "Suspect Two",
                "age": 35,
                "occupation": "Accountant",
                "relationship_to_victim": "Colleague",
                "public_profile": (
                    "Managed the victim's company accounts."
                ),
            },
            {
                "id": "suspect_three",
                "name": "Suspect Three",
                "age": 40,
                "occupation": "Consultant",
                "relationship_to_victim": "Advisor",
                "public_profile": (
                    "Advised the victim on company strategy."
                ),
            },
            {
                "id": "suspect_four",
                "name": "Suspect Four",
                "age": 29,
                "occupation": "Designer",
                "relationship_to_victim": "Employee",
                "public_profile": (
                    "Worked at the victim's company."
                ),
            },
        ],
        "initial_evidence": [
            {
                "id": "evidence_test_item",
                "title": "Broken Pen",
                "description": (
                    "A broken fountain pen was found beside the desk."
                ),
                "kind": "physical",
            }
        ],
    }


def test_load_case_returns_case_manifest(tmp_path) -> None:
    path = tmp_path / "case.json"

    path.write_text(
        json.dumps(valid_case_payload()),
        encoding="utf-8",
    )

    case = load_case(path)

    assert isinstance(case, CaseManifest)
    assert case.id == "case_loader_test"
    assert case.title == "Loader Test Case"
    assert len(case.suspects) == 4
    assert len(case.initial_evidence) == 1


def test_load_case_rejects_missing_file(tmp_path) -> None:
    path = tmp_path / "missing.json"

    with pytest.raises(
        CaseFileNotFoundError,
        match="does not exist",
    ):
        load_case(path)


def test_load_case_rejects_invalid_json(tmp_path) -> None:
    path = tmp_path / "broken.json"

    path.write_text(
        '{"id": "case_broken"',
        encoding="utf-8",
    )

    with pytest.raises(
        CaseJsonError,
        match="Invalid JSON",
    ):
        load_case(path)


def test_load_case_rejects_invalid_schema(tmp_path) -> None:
    payload = valid_case_payload()

    payload["id"] = "not_a_valid_case_id"

    path = tmp_path / "invalid_schema.json"

    path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    with pytest.raises(
        CaseSchemaError,
        match="does not match the case schema",
    ):
        load_case(path)


def test_load_case_rejects_wrong_suspect_count(
    tmp_path,
) -> None:
    payload = valid_case_payload()

    payload["suspects"] = payload["suspects"][:3]

    path = tmp_path / "three_suspects.json"

    path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    with pytest.raises(CaseSchemaError):
        load_case(path)