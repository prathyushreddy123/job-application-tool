from backend.automation.adapters.lever import (
    FIELD_MAP,
    LEVER_LABEL_MAP,
    LeverAdapter,
)


class TestLeverAdapter:
    def test_adapter_name(self):
        adapter = LeverAdapter()
        assert adapter.name == "lever"

    def test_field_map_has_core_fields(self):
        assert "name" in FIELD_MAP
        assert "email" in FIELD_MAP
        assert "phone" in FIELD_MAP
        assert "org" in FIELD_MAP
        assert "urls[LinkedIn]" in FIELD_MAP
        assert "urls[GitHub]" in FIELD_MAP
        assert "urls[Portfolio]" in FIELD_MAP
        assert "location" in FIELD_MAP
        assert "comments" in FIELD_MAP

    def test_field_map_dotpaths(self):
        assert FIELD_MAP["name"] == "personal.full_name"
        assert FIELD_MAP["email"] == "personal.email"
        assert FIELD_MAP["phone"] == "personal.phone"

    def test_label_map_has_lever_specific_entries(self):
        assert "full name" in LEVER_LABEL_MAP
        assert "additional information" in LEVER_LABEL_MAP
        assert "cover letter" in LEVER_LABEL_MAP
        assert "organization" in LEVER_LABEL_MAP

    def test_label_map_inherits_core_labels(self):
        # Should have all the shared Greenhouse labels too
        assert "first name" in LEVER_LABEL_MAP
        assert "last name" in LEVER_LABEL_MAP
        assert "email" in LEVER_LABEL_MAP
        assert "phone" in LEVER_LABEL_MAP
        assert "linkedin" in LEVER_LABEL_MAP

    def test_get_field_map(self):
        adapter = LeverAdapter()
        assert adapter.get_field_map() == FIELD_MAP

    def test_navigate_pages_returns_one(self):
        """Lever forms are single-page — navigate_pages should return 1."""
        import asyncio
        adapter = LeverAdapter()

        class FakePage:
            pass

        result = asyncio.get_event_loop().run_until_complete(
            adapter.navigate_pages(FakePage())
        )
        assert result == 1
