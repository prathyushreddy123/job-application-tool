import json
from pathlib import Path

from backend.automation.adapters.greenhouse import (
    FIELD_MAP,
    LABEL_MAP,
    GreenhouseAdapter,
    match_label_to_dotpath,
)
from backend.profile import get_answer


def _load_sample_profile() -> dict:
    return json.loads(Path("data/answers.json").read_text())


class TestFieldMap:
    def test_field_map_not_empty(self):
        assert len(FIELD_MAP) > 0

    def test_core_fields_present(self):
        """All essential Greenhouse fields should be in the map."""
        expected_dotpaths = {
            "personal.first_name",
            "personal.last_name",
            "personal.email",
            "personal.phone",
            "professional.linkedin_url",
        }
        actual_dotpaths = set(FIELD_MAP.values())
        assert expected_dotpaths.issubset(actual_dotpaths)

    def test_field_map_dotpaths_resolve(self):
        """Every dotpath in FIELD_MAP should resolve against the sample profile."""
        profile = _load_sample_profile()
        unresolved = []
        for field_name, dotpath in FIELD_MAP.items():
            value = get_answer(profile, dotpath)
            if value is None:
                unresolved.append(f"{field_name} -> {dotpath}")

        assert unresolved == [], f"Unresolved dotpaths: {unresolved}"


class TestLabelMap:
    def test_label_map_not_empty(self):
        assert len(LABEL_MAP) > 0

    def test_label_map_dotpaths_resolve(self):
        """Every dotpath in LABEL_MAP should resolve against the sample profile."""
        profile = _load_sample_profile()
        unresolved = []
        for label, dotpath in LABEL_MAP.items():
            value = get_answer(profile, dotpath)
            if value is None:
                unresolved.append(f"{label} -> {dotpath}")

        assert unresolved == [], f"Unresolved dotpaths: {unresolved}"


class TestMatchLabel:
    def test_exact_match(self):
        assert match_label_to_dotpath("First Name") == "personal.first_name"

    def test_case_insensitive(self):
        assert match_label_to_dotpath("EMAIL") == "personal.email"

    def test_with_colon(self):
        assert match_label_to_dotpath("Phone Number:") == "personal.phone"

    def test_with_asterisk(self):
        assert match_label_to_dotpath("Email *") == "personal.email"

    def test_substring_match(self):
        assert match_label_to_dotpath("Your LinkedIn Profile URL") == "professional.linkedin_url"

    def test_no_match(self):
        assert match_label_to_dotpath("Favorite Programming Language") is None

    def test_empty_string(self):
        assert match_label_to_dotpath("") is None

    def test_sponsorship_variations(self):
        assert match_label_to_dotpath("Do you require visa sponsorship?") == "work_authorization.sponsorship_required"

    def test_salary_variations(self):
        assert match_label_to_dotpath("What is your desired salary?") == "preferences.salary_expectation"

    def test_relocate(self):
        assert match_label_to_dotpath("Are you willing to relocate?") == "preferences.willing_to_relocate"


class TestGreenhouseAdapter:
    def test_adapter_name(self):
        adapter = GreenhouseAdapter()
        assert adapter.name == "greenhouse"

    def test_get_field_map(self):
        adapter = GreenhouseAdapter()
        field_map = adapter.get_field_map()
        assert field_map is FIELD_MAP
        assert len(field_map) > 0
