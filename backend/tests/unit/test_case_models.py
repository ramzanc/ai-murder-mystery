import pytest
from pydantic import ValidationError

from app.domain.case import (
    AccusationOptions,
    CanonicalSolution,
    CaseManifest,
    Difficulty,
    PublicDossier,
    Victim,
)
from app.domain.evidence import Evidence, EvidenceKind
from app.domain.suspect import Suspect

from app.domain.timeline import (
    ClockTime,
    TimeInterval,
    Timeline,
    TimelineEvent,
    TimelineEventKind,
    TimelineLocation,
)


def make_suspect(
    suspect_id: str,
    name: str,
) -> Suspect:
    return Suspect(
        id=suspect_id,
        name=name,
        age=35,
        occupation="Hotel employee",
        relationship_to_victim="Knew the victim",
        public_profile=f"{name} was present at the hotel that evening.",
    )


def make_case() -> CaseManifest:
    return CaseManifest(
        id="case_last_meeting",
        title="The Last Meeting",
        difficulty=Difficulty.MEDIUM,
        dossier=PublicDossier(
            summary=(
                "Evelyn Cross was found dead shortly after "
                "a private evening meeting."
            ),
            location="The Ashcroft Hotel",
            incident_time="9:30 PM",
        ),
        victim=Victim(
            id="victim_evelyn_cross",
            name="Evelyn Cross",
            age=47,
            public_profile=(
                "Evelyn was the owner of the Ashcroft Hotel "
                "and had called an unusual private meeting."
            ),
        ),
        suspects=(
            make_suspect(
                "suspect_marcus_hale",
                "Marcus Hale",
            ),
            make_suspect(
                "suspect_iris_vale",
                "Iris Vale",
            ),
            make_suspect(
                "suspect_daniel_reed",
                "Daniel Reed",
            ),
            make_suspect(
                "suspect_nora_bell",
                "Nora Bell",
            ),
        ),
        initial_evidence=(
            Evidence(
                id="evidence_broken_watch",
                title="Broken Watch",
                description=(
                    "A damaged wristwatch was recovered "
                    "near the victim."
                ),
                kind=EvidenceKind.PHYSICAL,
            ),
            Evidence(
                id="evidence_access_log",
                title="Door Access Log",
                description=(
                    "The hotel's electronic access system "
                    "recorded several entries that evening."
                ),
                kind=EvidenceKind.DIGITAL,
            ),
        ),
                timeline=Timeline(
            murder_window=TimeInterval(
                start=ClockTime(hour=21, minute=20),
                end=ClockTime(hour=21, minute=40),
            ),
            locations=(
                TimelineLocation(
                    id="location_private_office",
                    name="Private office",
                ),
            ),
            events=(
                TimelineEvent(
                    id="timeline_event_murder",
                    kind=TimelineEventKind.MURDER,
                    description=(
                        "Marcus killed Evelyn in the private office."
                    ),
                    actor_ids=(
                        "victim_evelyn_cross",
                        "suspect_marcus_hale",
                    ),
                    location_id="location_private_office",
                    interval=TimeInterval(
                        start=ClockTime(hour=21, minute=29),
                        end=ClockTime(hour=21, minute=30),
                    ),
                ),
            ),
        ),
        accusation_options=AccusationOptions(
            motives=(
                "The victim discovered missing company funds.",
                "A personal grudge.",
            ),
            methods=(
                "The victim was struck with a desk ornament.",
                "The victim was poisoned.",
            ),
        ),
        solution=CanonicalSolution(
            killer_id="suspect_marcus_hale",
            motive="The victim discovered missing company funds.",
            method="The victim was struck with a desk ornament.",
            key_evidence_ids=(
                "evidence_broken_watch",
                "evidence_access_log",
            ),
            explanation=(
                "The broken watch and access log identify the killer."
            ),
        ),
    )


def test_valid_four_suspect_case_constructs() -> None:
    case = make_case()

    assert case.id == "case_last_meeting"
    assert case.title == "The Last Meeting"
    assert case.difficulty == Difficulty.MEDIUM

    assert case.victim.name == "Evelyn Cross"

    assert len(case.suspects) == 4
    assert len(case.initial_evidence) == 2


@pytest.mark.parametrize(
    "suspects",
    [
        (),
        (
            make_suspect(
                "suspect_one",
                "One",
            ),
            make_suspect(
                "suspect_two",
                "Two",
            ),
            make_suspect(
                "suspect_three",
                "Three",
            ),
        ),
        (
            make_suspect(
                "suspect_one",
                "One",
            ),
            make_suspect(
                "suspect_two",
                "Two",
            ),
            make_suspect(
                "suspect_three",
                "Three",
            ),
            make_suspect(
                "suspect_four",
                "Four",
            ),
            make_suspect(
                "suspect_five",
                "Five",
            ),
        ),
    ],
)
def test_case_requires_exactly_four_suspects(
    suspects: tuple[Suspect, ...],
) -> None:
    with pytest.raises(ValidationError):
        CaseManifest(
            id="case_invalid_count",
            title="Invalid Suspect Count",
            difficulty=Difficulty.EASY,
            dossier=PublicDossier(
                summary="A test case.",
                location="Test location",
                incident_time="10:00 PM",
            ),
            victim=Victim(
                id="victim_test",
                name="Test Victim",
                age=40,
                public_profile="A test victim.",
            ),
            suspects=suspects,  # pyright: ignore[reportArgumentType]
            accusation_options=AccusationOptions(
                motives=("A test motive.", "Another motive."),
                methods=("A test method.", "Another method."),
            ),
            timeline=Timeline(
                murder_window=TimeInterval(
                    start=ClockTime(hour=21, minute=20),
                    end=ClockTime(hour=21, minute=40),
                ),
                locations=(
                    TimelineLocation(
                        id="location_private_office",
                        name="Private office",
                    ),
                ),
                events=(
                    TimelineEvent(
                        id="timeline_event_murder",
                        kind=TimelineEventKind.MURDER,
                        description=(
                            "Marcus killed Evelyn in the private office."
                        ),
                        actor_ids=(
                            "victim_evelyn_cross",
                            "suspect_marcus_hale",
                        ),
                        location_id="location_private_office",
                        interval=TimeInterval(
                            start=ClockTime(hour=21, minute=29),
                            end=ClockTime(hour=21, minute=30),
                        ),
                    ),
                ),
            ),
            solution=CanonicalSolution(
                killer_id="suspect_one",
                motive="A test motive.",
                method="A test method.",
                key_evidence_ids=(
                    "evidence_one",
                    "evidence_two",
                ),
                explanation="A test explanation.",
            ),
        )


def test_unknown_suspect_fields_are_rejected() -> None:
    with pytest.raises(ValidationError):
        Suspect(
            id="suspect_marcus_hale",
            name="Marcus Hale",
            age=35,
            occupation="Accountant",
            relationship_to_victim="Business partner",
            public_profile="Worked with the victim.",
            secret_field="this should not exist",  # pyright: ignore[reportCallIssue]
        )


@pytest.mark.parametrize(
    "invalid_id",
    [
        "marcus",
        "evidence_marcus",
        "Suspect_Marcus",
        "suspect-marcus",
        "",
    ],
)
def test_malformed_suspect_ids_are_rejected(
    invalid_id: str,
) -> None:
    with pytest.raises(ValidationError):
        Suspect(
            id=invalid_id,
            name="Marcus Hale",
            age=35,
            occupation="Accountant",
            relationship_to_victim="Business partner",
            public_profile="Worked with the victim.",
        )


def test_duplicate_suspect_ids_are_rejected() -> None:
    duplicate = make_suspect(
        "suspect_duplicate",
        "First Person",
    )

    with pytest.raises(
        ValidationError,
        match="suspect IDs must be unique",
    ):
        CaseManifest(
            id="case_duplicate_suspects",
            title="Duplicate Suspect IDs",
            difficulty=Difficulty.MEDIUM,
            dossier=PublicDossier(
                summary="A test case.",
                location="Test location",
                incident_time="10:00 PM",
            ),
            victim=Victim(
                id="victim_test",
                name="Test Victim",
                age=40,
                public_profile="A test victim.",
            ),
            suspects=(
                duplicate,
                make_suspect(
                    "suspect_two",
                    "Second Person",
                ),
                make_suspect(
                    "suspect_three",
                    "Third Person",
                ),
                duplicate,
            ),
            accusation_options=AccusationOptions(
                motives=("A test motive.", "Another motive."),
                methods=("A test method.", "Another method."),
            ),
            timeline=Timeline(
                murder_window=TimeInterval(
                    start=ClockTime(hour=21, minute=20),
                    end=ClockTime(hour=21, minute=40),
                ),
                locations=(
                    TimelineLocation(
                        id="location_private_office",
                        name="Private office",
                    ),
                ),
                events=(
                    TimelineEvent(
                        id="timeline_event_murder",
                        kind=TimelineEventKind.MURDER,
                        description=(
                            "Marcus killed Evelyn in the private office."
                        ),
                        actor_ids=(
                            "victim_evelyn_cross",
                            "suspect_marcus_hale",
                        ),
                        location_id="location_private_office",
                        interval=TimeInterval(
                            start=ClockTime(hour=21, minute=29),
                            end=ClockTime(hour=21, minute=30),
                        ),
                    ),
                ),
            ),
            solution=CanonicalSolution(
                killer_id="suspect_duplicate",
                motive="A test motive.",
                method="A test method.",
                key_evidence_ids=(
                    "evidence_one",
                    "evidence_two",
                ),
                explanation="A test explanation.",
            ),
        )


def test_duplicate_evidence_ids_are_rejected() -> None:
    case_data = make_case().model_dump()

    case_data["initial_evidence"] = (
        {
            "id": "evidence_duplicate",
            "title": "First Evidence",
            "description": "First evidence description.",
            "kind": "physical",
        },
        {
            "id": "evidence_duplicate",
            "title": "Second Evidence",
            "description": "Second evidence description.",
            "kind": "digital",
        },
    )

    with pytest.raises(
        ValidationError,
        match="evidence IDs must be unique",
    ):
        CaseManifest.model_validate(case_data)


def test_solution_references_case_suspect_and_evidence() -> None:
    case_data = make_case().model_dump()
    case_data["solution"]["killer_id"] = "suspect_unknown"

    with pytest.raises(
        ValidationError,
        match="solution killer_id must reference a case suspect",
    ):
        CaseManifest.model_validate(case_data)

    case_data = make_case().model_dump()
    case_data["solution"]["key_evidence_ids"] = (
        "evidence_broken_watch",
        "evidence_unknown",
    )

    with pytest.raises(
        ValidationError,
        match="solution key evidence must reference case evidence",
    ):
        CaseManifest.model_validate(case_data)


def test_solution_key_evidence_ids_are_unique() -> None:
    case_data = make_case().model_dump()
    case_data["solution"]["key_evidence_ids"] = (
        "evidence_broken_watch",
        "evidence_broken_watch",
    )

    with pytest.raises(
        ValidationError,
        match="solution key evidence IDs must be unique",
    ):
        CaseManifest.model_validate(case_data)


def test_solution_motive_and_method_are_offered_options() -> None:
    case_data = make_case().model_dump()
    case_data["solution"]["motive"] = "A motive that was not offered."

    with pytest.raises(
        ValidationError,
        match="solution motive must be present in accusation options",
    ):
        CaseManifest.model_validate(case_data)

    case_data = make_case().model_dump()
    case_data["solution"]["method"] = "A method that was not offered."

    with pytest.raises(
        ValidationError,
        match="solution method must be present in accusation options",
    ):
        CaseManifest.model_validate(case_data)


def test_case_definition_is_immutable() -> None:
    case = make_case()

    with pytest.raises(ValidationError):
        case.title = "A Different Murder"  # pyright: ignore[reportAttributeAccessIssue]


def test_nested_suspect_is_immutable() -> None:
    case = make_case()

    with pytest.raises(ValidationError):
        case.suspects[0].name = "Changed Name"  # pyright: ignore[reportAttributeAccessIssue]


def test_suspect_collection_cannot_be_mutated() -> None:
    case = make_case()

    assert isinstance(case.suspects, tuple)

    with pytest.raises(AttributeError):
        case.suspects.append(  # pyright: ignore[reportAttributeAccessIssue]
            make_suspect(
                "suspect_fifth",
                "Fifth Person",
            )
        )
