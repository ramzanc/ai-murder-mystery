from typing import Any

from pydantic import BaseModel

from app.application.investigation_service import (
    InvestigationError,
    ask_question,
    start_session,
)
from app.domain.case import CaseManifest
from app.domain.investigation import (
    InvestigationSession,
    QuestionTopic,
)


def render_case_header(case: CaseManifest) -> None:
    print()
    print("=" * 72)
    print(case.title)
    print("=" * 72)
    print(f"Case ID: {case.id}")
    print(f"Difficulty: {case.difficulty}")
    print()


def render_dossier(case: CaseManifest) -> None:
    print()
    print("--- CASE DOSSIER ---")
    _render_value(case.dossier)
    print()


def render_victim(case: CaseManifest) -> None:
    print()
    print("--- VICTIM ---")
    _render_value(case.victim)
    print()


def render_suspects(case: CaseManifest) -> None:
    print()
    print("--- SUSPECTS ---")

    for index, suspect in enumerate(case.suspects, start=1):
        print()
        print(f"{index}. {suspect.name}")
        print(f"   ID: {suspect.id}")
        print(f"   Age: {suspect.age}")
        print(f"   Occupation: {suspect.occupation}")
        print(
            "   Relationship to victim: "
            f"{suspect.relationship_to_victim}"
        )
        print(f"   Public profile: {suspect.public_profile}")

    print()


def render_evidence(case: CaseManifest) -> None:
    print()
    print("--- STARTING EVIDENCE ---")

    if not case.initial_evidence:
        print("No starting evidence.")
        print()
        return

    for index, evidence in enumerate(
        case.initial_evidence,
        start=1,
    ):
        print()
        print(f"{index}. {evidence.title}")
        print(f"   ID: {evidence.id}")
        print(f"   Kind: {evidence.kind}")
        print(f"   {evidence.description}")

    print()


def render_discovered_evidence(
    case: CaseManifest,
    session: InvestigationSession,
) -> None:
    print()
    print("--- DISCOVERED EVIDENCE ---")

    discovered_ids = set(session.discovered_evidence_ids)

    discovered = [
        evidence
        for evidence in case.initial_evidence
        if str(evidence.id) in discovered_ids
    ]

    if not discovered:
        print("You have not discovered any evidence yet.")
        print()
        return

    for index, evidence in enumerate(discovered, start=1):
        print()
        print(f"{index}. {evidence.title}")
        print(f"   ID: {evidence.id}")
        print(f"   Kind: {evidence.kind}")
        print(f"   {evidence.description}")

    print()


def render_investigation_history(
    session: InvestigationSession,
) -> None:
    print()
    print("--- INVESTIGATION HISTORY ---")

    if not session.events:
        print("No questions asked yet.")
        print()
        return

    for event in session.events:
        print()
        print(
            f"{event.sequence}. "
            f"[{event.topic.value.upper()}] "
            f"{event.suspect_id}"
        )
        print(f"   Detective: {event.question}")
        print(f"   Response:  {event.answer}")

    print()


def run_case_browser(case: CaseManifest) -> None:
    session = start_session(case)
    print("CASE OBJECT:")

    render_case_header(case)

    while True:
        print("What would you like to do?")
        print("1. View dossier")
        print("2. View victim")
        print("3. View suspects")
        print("4. View discovered evidence")
        print("5. Question a suspect")
        print("6. View investigation history")
        print("0. Exit")

        choice = input("> ").strip()

        if choice == "1":
            render_dossier(case)

        elif choice == "2":
            render_victim(case)

        elif choice == "3":
            render_suspects(case)

        elif choice == "4":
            render_discovered_evidence(
                case,
                session,
            )

        elif choice == "5":
            session = _question_suspect_interactively(
                case,
                session,
            )

        elif choice == "6":
            render_investigation_history(session)

        elif choice == "0":
            print()
            print("Investigation closed.")
            return

        else:
            print()
            print("Invalid option. Choose one of the menu numbers.")
            print()


def _question_suspect_interactively(
    case: CaseManifest,
    session: InvestigationSession,
) -> InvestigationSession:
    print()
    print("--- QUESTION A SUSPECT ---")

    for index, suspect in enumerate(case.suspects, start=1):
        print(
            f"{index}. {suspect.name} "
            f"({suspect.id})"
        )

    suspect_choice = input(
        "Choose a suspect number: "
    ).strip()

    try:
        suspect_index = int(suspect_choice) - 1
    except ValueError:
        print()
        print("Invalid suspect selection.")
        print()
        return session

    if not 0 <= suspect_index < len(case.suspects):
        print()
        print("Invalid suspect selection.")
        print()
        return session

    suspect = case.suspects[suspect_index]

    print()
    print("Choose a topic:")
    print("1. Alibi")
    print("2. Secret")

    topic_choice = input("> ").strip()

    topic_by_choice = {
        "1": QuestionTopic.ALIBI,
        "2": QuestionTopic.SECRET,
    }

    topic = topic_by_choice.get(topic_choice)

    if topic is None:
        print()
        print("Invalid question topic.")
        print()
        return session

    try:
        updated_session = ask_question(
            case=case,
            session=session,
            suspect_id=str(suspect.id),
            topic=topic,
        )
    except InvestigationError as exc:
        print()
        print(f"Unable to perform action: {exc}")
        print()
        return session

    event = updated_session.events[-1]

    print()
    print(f"Detective: {event.question}")
    print(f"{event.answer}")
    print()

    return updated_session


def _render_value(
    value: Any,
    indent: int = 0,
) -> None:
    prefix = " " * indent

    if isinstance(value, BaseModel):
        data = value.model_dump(mode="python")

        for key, nested_value in data.items():
            label = _humanize(key)

            if isinstance(
                nested_value,
                (dict, list, tuple),
            ):
                print(f"{prefix}{label}:")
                _render_value(
                    nested_value,
                    indent + 2,
                )
            else:
                print(
                    f"{prefix}{label}: "
                    f"{nested_value}"
                )

        return

    if isinstance(value, dict):
        for key, nested_value in value.items():
            label = _humanize(str(key))

            if isinstance(
                nested_value,
                (dict, list, tuple),
            ):
                print(f"{prefix}{label}:")
                _render_value(
                    nested_value,
                    indent + 2,
                )
            else:
                print(
                    f"{prefix}{label}: "
                    f"{nested_value}"
                )

        return

    if isinstance(value, (list, tuple)):
        for item in value:
            print(f"{prefix}-", end=" ")

            if isinstance(
                item,
                (dict, list, tuple),
            ):
                print()
                _render_value(
                    item,
                    indent + 2,
                )
            else:
                print(item)

        return

    print(f"{prefix}{value}")


def _humanize(value: str) -> str:
    return value.replace("_", " ").title()