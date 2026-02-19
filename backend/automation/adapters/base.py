from abc import ABC, abstractmethod

from backend.models.job import FilledField


class BaseAdapter(ABC):
    """Abstract base class for ATS form-filling adapters."""

    name: str = "base"

    @abstractmethod
    async def detect(self, page) -> bool:
        """Return True if this adapter can handle the current page."""

    @abstractmethod
    def get_field_map(self) -> dict[str, str]:
        """Return mapping of {form_field_identifier: answers.json dotpath}."""

    @abstractmethod
    async def fill_form(self, page, profile: dict) -> list[FilledField]:
        """Fill form fields on the page using profile data.

        Returns a list of FilledField entries describing what was filled.
        """

    @abstractmethod
    async def navigate_pages(self, page) -> int:
        """Handle multi-page form navigation.

        Click 'Next' buttons through all pages, filling each one.
        Returns the total number of pages processed.
        """

    @abstractmethod
    async def submit(self, page) -> bool:
        """Click the submit button.

        Returns True on success, False on failure.
        Should NOT be called in dry-run mode.
        """

    @abstractmethod
    async def detect_custom_questions(self, page) -> list[dict]:
        """Find non-standard form fields (custom free-text questions).

        Returns a list of dicts: [{"label": "...", "selector": "..."}]
        """
