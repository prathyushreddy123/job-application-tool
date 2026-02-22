from backend.automation.adapters.workday import (
    FIELD_MAP,
    WORKDAY_LABEL_MAP,
    WorkdayAdapter,
)


class TestWorkdayAdapter:
    def test_adapter_name(self):
        adapter = WorkdayAdapter()
        assert adapter.name == "workday"

    def test_field_map_uses_automation_ids(self):
        """Workday FIELD_MAP keys should be data-automation-id values."""
        assert "firstName" in FIELD_MAP
        assert "lastName" in FIELD_MAP
        assert "email" in FIELD_MAP
        assert "phone-number" in FIELD_MAP
        assert "addressLine1" in FIELD_MAP
        assert "city" in FIELD_MAP
        assert "postalCode" in FIELD_MAP
        assert "currentEmployer" in FIELD_MAP
        assert "jobTitle" in FIELD_MAP

    def test_field_map_dotpaths(self):
        assert FIELD_MAP["firstName"] == "personal.first_name"
        assert FIELD_MAP["lastName"] == "personal.last_name"
        assert FIELD_MAP["email"] == "personal.email"
        assert FIELD_MAP["phone-number"] == "personal.phone"
        assert FIELD_MAP["currentEmployer"] == "professional.current_company"

    def test_label_map_has_workday_specific_entries(self):
        assert "legal first name" in WORKDAY_LABEL_MAP
        assert "legal last name" in WORKDAY_LABEL_MAP
        assert "preferred first name" in WORKDAY_LABEL_MAP
        assert "address line 1" in WORKDAY_LABEL_MAP
        assert "postal code" in WORKDAY_LABEL_MAP

    def test_label_map_inherits_core_labels(self):
        assert "first name" in WORKDAY_LABEL_MAP
        assert "last name" in WORKDAY_LABEL_MAP
        assert "email" in WORKDAY_LABEL_MAP
        assert "phone" in WORKDAY_LABEL_MAP
        assert "linkedin" in WORKDAY_LABEL_MAP

    def test_get_field_map(self):
        adapter = WorkdayAdapter()
        assert adapter.get_field_map() == FIELD_MAP

    def test_field_map_no_name_collisions_with_input_names(self):
        """Workday uses data-automation-id, not input name attributes.
        Keys should be camelCase automation IDs, not HTML names."""
        for key in FIELD_MAP:
            # Should not have brackets or underscores (those are Greenhouse-style)
            assert "[" not in key
            assert "]" not in key
