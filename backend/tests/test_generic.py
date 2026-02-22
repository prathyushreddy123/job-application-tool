from backend.automation.adapters.generic import (
    FIELD_MAP,
    LABEL_MAP,
    GenericAdapter,
    _match_generic_label,
)


class TestGenericAdapter:
    def test_adapter_name(self):
        adapter = GenericAdapter()
        assert adapter.name == "generic"

    def test_field_map_is_empty(self):
        assert FIELD_MAP == {}

    def test_get_field_map_is_empty(self):
        adapter = GenericAdapter()
        assert adapter.get_field_map() == {}

    def test_detect_always_true(self):
        import asyncio
        adapter = GenericAdapter()

        class FakePage:
            pass

        result = asyncio.get_event_loop().run_until_complete(
            adapter.detect(FakePage())
        )
        assert result is True

    def test_label_map_has_name_variants(self):
        assert "full name" in LABEL_MAP
        assert "name" in LABEL_MAP
        assert "your name" in LABEL_MAP
        assert "first name" in LABEL_MAP
        assert "last name" in LABEL_MAP

    def test_label_map_has_contact_fields(self):
        assert "email" in LABEL_MAP
        assert "email address" in LABEL_MAP
        assert "phone" in LABEL_MAP
        assert "telephone" in LABEL_MAP
        assert "mobile" in LABEL_MAP

    def test_label_map_has_education_fields(self):
        assert "degree" in LABEL_MAP
        assert "university" in LABEL_MAP
        assert "school" in LABEL_MAP
        assert "major" in LABEL_MAP

    def test_label_map_has_professional_fields(self):
        assert "linkedin" in LABEL_MAP
        assert "github" in LABEL_MAP
        assert "current company" in LABEL_MAP
        assert "job title" in LABEL_MAP

    def test_match_generic_label_exact(self):
        assert _match_generic_label("Email") == "personal.email"
        assert _match_generic_label("Full Name") == "personal.full_name"

    def test_match_generic_label_with_colon(self):
        assert _match_generic_label("Email:") == "personal.email"
        assert _match_generic_label("Phone Number *:") == "personal.phone"

    def test_match_generic_label_substring(self):
        assert _match_generic_label("Your Email Address Here") == "personal.email"

    def test_match_generic_label_no_match(self):
        assert _match_generic_label("xyzzy") is None

    def test_label_map_education_uses_list_index(self):
        """Education dotpaths should use list indexing (education.0.degree)."""
        assert LABEL_MAP["degree"] == "education.0.degree"
        assert LABEL_MAP["university"] == "education.0.school"
        assert LABEL_MAP["major"] == "education.0.major"
