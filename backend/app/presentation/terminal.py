from app.domain.case import CaseManifest


SEPARATOR = "=" * 60


def render_case_header(case: CaseManifest) -> None:
    """Print the case title and basic metadata."""

    print()
    print(SEPARATOR)
    print(case.title.upper().center(60))
    print(SEPARATOR)
    print()
    print(f"Difficulty: {case.difficulty.value.upper()}")
    print()


def render_dossier(case: CaseManifest) -> None:
    """Display the player-visible public dossier."""

    print()
    print(SEPARATOR)
    print("CASE DOSSIER")
    print(SEPARATOR)

    print(f"\nCase: {case.title}")
    print(f"Location: {case.dossier.location}")
    print(f"Incident time: {case.dossier.incident_time}")

    print("\nSummary")
    print("-" * 60)
    print(case.dossier.summary)

    print("\nVictim")
    print("-" * 60)
    print(f"Name: {case.victim.name}")
    print(f"Age: {case.victim.age}")
    print(case.victim.public_profile)


def render_suspects(case: CaseManifest) -> None:
    """Display all suspects in the case."""

    print()
    print(SEPARATOR)
    print("SUSPECTS")
    print(SEPARATOR)

    for index, suspect in enumerate(case.suspects, start=1):
        print()
        print(f"{index}. {suspect.name}")
        print("-" * 60)
        print(f"Age: {suspect.age}")
        print(f"Occupation: {suspect.occupation}")
        print(
            "Relationship to victim: "
            f"{suspect.relationship_to_victim}"
        )
        print()
        print(suspect.public_profile)


def render_evidence(case: CaseManifest) -> None:
    """Display evidence available at the beginning of the case."""

    print()
    print(SEPARATOR)
    print("STARTING EVIDENCE")
    print(SEPARATOR)

    if not case.initial_evidence:
        print("\nNo evidence is available yet.")
        return

    for index, evidence in enumerate(
        case.initial_evidence,
        start=1,
    ):
        print()
        print(f"{index}. {evidence.title}")
        print("-" * 60)
        print(f"Type: {evidence.kind.value.title()}")
        print(evidence.description)


def run_case_browser(case: CaseManifest) -> None:
    """Run the interactive terminal dossier browser."""

    render_case_header(case)

    while True:
        print("1. View case dossier")
        print("2. View suspects")
        print("3. View starting evidence")
        print("q. Quit")

        choice = input("\nChoose an option: ").strip().lower()

        if choice == "1":
            render_dossier(case)

        elif choice == "2":
            render_suspects(case)

        elif choice == "3":
            render_evidence(case)

        elif choice in {"q", "quit"}:
            print("\nInvestigation closed.")
            return

        else:
            print(
                "\nInvalid choice. "
                "Enter 1, 2, 3, or q."
            )

        input("\nPress Enter to return to the menu...")
        print()