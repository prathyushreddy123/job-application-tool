import logging
from urllib.parse import urlparse

from backend.models.job import FilledField
from backend.profile import get_answer
from backend.automation.adapters.base import BaseAdapter

logger = logging.getLogger(__name__)

# Greenhouse form field name/id -> answers.json dotpath
# Based on Greenhouse's standard job application form structure
FIELD_MAP: dict[str, str] = {
    # Personal info
    "first_name": "personal.first_name",
    "last_name": "personal.last_name",
    "email": "personal.email",
    "phone": "personal.phone",
    # Professional links
    "job_application[location]": "personal.address.city",
    "job_application[phone]": "personal.phone",
    "job_application[first_name]": "personal.first_name",
    "job_application[last_name]": "personal.last_name",
    "job_application[email]": "personal.email",
    # URLs
    "linkedin_profile_url": "professional.linkedin_url",
    "job_application[urls][LinkedIn]": "professional.linkedin_url",
    "job_application[urls][Portfolio]": "professional.portfolio_url",
    "job_application[urls][GitHub]": "professional.github_url",
    "website_url": "professional.portfolio_url",
    "github_url": "professional.github_url",
}

# Common Greenhouse label text -> answers.json dotpath (fallback matching)
LABEL_MAP: dict[str, str] = {
    "first name": "personal.first_name",
    "last name": "personal.last_name",
    "email": "personal.email",
    "phone": "personal.phone",
    "phone number": "personal.phone",
    "mobile": "personal.phone",
    "cell phone": "personal.phone",
    "contact number": "personal.phone",
    "linkedin": "professional.linkedin_url",
    "linkedin url": "professional.linkedin_url",
    "linkedin profile": "professional.linkedin_url",
    "portfolio": "professional.portfolio_url",
    "portfolio url": "professional.portfolio_url",
    "website": "professional.portfolio_url",
    "website url": "professional.portfolio_url",
    "github": "professional.github_url",
    "github url": "professional.github_url",
    "city": "personal.address.city",
    "state": "personal.address.state",
    "zip": "personal.address.zip",
    "zip code": "personal.address.zip",
    "street address": "personal.address.street",
    "country": "personal.address.country",
    "location": "personal.address.city",
    "current company": "professional.current_company",
    "current title": "professional.current_title",
    "years of experience": "professional.years_experience",
    "years experience": "professional.years_experience",
    # Work authorization
    "authorized to work": "work_authorization.authorized_us",
    "work authorization": "work_authorization.authorized_us",
    "sponsorship": "work_authorization.sponsorship_required",
    "require sponsorship": "work_authorization.sponsorship_required",
    "visa sponsorship": "work_authorization.sponsorship_required",
    # Demographics (EEO)
    "gender": "demographics.gender",
    "race": "demographics.ethnicity",
    "ethnicity": "demographics.ethnicity",
    "veteran": "demographics.veteran_status",
    "veteran status": "demographics.veteran_status",
    "disability": "demographics.disability_status",
    "disability status": "demographics.disability_status",
    # Preferences
    "salary": "preferences.salary_expectation",
    "salary expectation": "preferences.salary_expectation",
    "desired salary": "preferences.salary_expectation",
    "compensation": "preferences.salary_expectation",
    "start date": "preferences.available_start",
    "available start date": "preferences.available_start",
    "earliest start date": "preferences.available_start",
    "willing to relocate": "preferences.willing_to_relocate",
    "relocate": "preferences.willing_to_relocate",
    "remote": "preferences.work_preference",
    "work preference": "preferences.work_preference",
}


def match_label_to_dotpath(label: str) -> str | None:
    """Match a form field label to an answers.json dotpath using LABEL_MAP."""
    normalized = label.lower().strip().rstrip(":").rstrip("*").strip()

    # Exact match
    if normalized in LABEL_MAP:
        return LABEL_MAP[normalized]

    # Substring match: find the longest matching key
    best_match = None
    best_len = 0
    for key, dotpath in LABEL_MAP.items():
        if key in normalized and len(key) > best_len:
            best_match = dotpath
            best_len = len(key)

    return best_match


class GreenhouseAdapter(BaseAdapter):
    """Adapter for Greenhouse ATS job application forms."""

    name = "greenhouse"

    async def detect(self, page) -> bool:
        """Detect if the current page is a Greenhouse application."""
        url = page.url
        if _is_greenhouse_url(url):
            return True

        # Check for Greenhouse markers in the page HTML
        try:
            greenhouse_marker = await page.query_selector(
                "#grnhse_app, [data-greenhouse], .greenhouse-job-board"
            )
            return greenhouse_marker is not None
        except Exception:
            return False

    def get_field_map(self) -> dict[str, str]:
        return FIELD_MAP

    async def fill_form(self, page, profile: dict) -> list[FilledField]:
        """Fill all detectable form fields on the current page."""
        results: list[FilledField] = []

        # Fill fields by name/id attribute (FIELD_MAP)
        for field_name, dotpath in FIELD_MAP.items():
            value = get_answer(profile, dotpath)
            if value is None:
                continue

            selector = f'input[name="{field_name}"], textarea[name="{field_name}"]'
            element = await page.query_selector(selector)
            if element is None:
                # Try by id
                selector = f'#{field_name}'
                element = await page.query_selector(selector)

            if element is not None:
                try:
                    await element.fill(value)
                    results.append(FilledField(
                        label=field_name,
                        value=value,
                        status="filled",
                        source=dotpath,
                    ))
                except Exception as e:
                    logger.warning(f"Failed to fill {field_name}: {e}")
                    results.append(FilledField(
                        label=field_name,
                        value="",
                        status="failed",
                        source=dotpath,
                    ))

        # Fill fields by label text (LABEL_MAP fallback)
        labels = await page.query_selector_all("label")
        for label_el in labels:
            label_text = (await label_el.inner_text()).strip()
            dotpath = match_label_to_dotpath(label_text)
            if dotpath is None:
                continue

            # Skip if already filled via FIELD_MAP
            if any(f.source == dotpath and f.status == "filled" for f in results):
                continue

            value = get_answer(profile, dotpath)
            if value is None:
                continue

            # Find the associated input
            for_attr = await label_el.get_attribute("for")
            if for_attr:
                input_el = await page.query_selector(f"#{for_attr}")
            else:
                input_el = await label_el.query_selector("input, textarea, select")

            if input_el is not None:
                try:
                    tag = await input_el.evaluate("el => el.tagName.toLowerCase()")
                    if tag == "select":
                        await _fill_select(input_el, value)
                    else:
                        await input_el.fill(value)
                    results.append(FilledField(
                        label=label_text,
                        value=value,
                        status="filled",
                        source=dotpath,
                    ))
                except Exception as e:
                    logger.warning(f"Failed to fill '{label_text}': {e}")
                    results.append(FilledField(
                        label=label_text,
                        value="",
                        status="failed",
                        source=dotpath,
                    ))

        return results

    async def navigate_pages(self, page) -> int:
        """Handle multi-page Greenhouse forms by clicking Next buttons."""
        page_count = 1

        while True:
            next_btn = await page.query_selector(
                'button:has-text("Next"), '
                'input[type="submit"][value*="Next"], '
                'a:has-text("Next")'
            )
            if next_btn is None:
                break

            try:
                await next_btn.click()
                await page.wait_for_load_state("networkidle")
                page_count += 1
            except Exception as e:
                logger.warning(f"Failed to navigate to next page: {e}")
                break

        return page_count

    async def submit(self, page) -> bool:
        """Click the Greenhouse submit button."""
        try:
            submit_btn = await page.query_selector(
                '#submit_app, '
                'button[type="submit"]:has-text("Submit"), '
                'input[type="submit"][value*="Submit"]'
            )
            if submit_btn is None:
                logger.error("Submit button not found")
                return False

            await submit_btn.click()
            await page.wait_for_load_state("networkidle")
            return True
        except Exception as e:
            logger.error(f"Submit failed: {e}")
            return False

    async def detect_custom_questions(self, page) -> list[dict]:
        """Find custom free-text questions on Greenhouse forms.

        These are typically textareas or inputs with labels that don't
        match any known field patterns.
        """
        custom = []
        labels = await page.query_selector_all("label")

        for label_el in labels:
            label_text = (await label_el.inner_text()).strip()
            if not label_text or len(label_text) < 5:
                continue

            # Skip if it matches a known field
            if match_label_to_dotpath(label_text) is not None:
                continue

            for_attr = await label_el.get_attribute("for")
            if for_attr:
                input_el = await page.query_selector(f"#{for_attr}")
            else:
                input_el = await label_el.query_selector("textarea, input[type='text']")

            if input_el is not None:
                tag = await input_el.evaluate("el => el.tagName.toLowerCase()")
                if tag in ("textarea", "input"):
                    selector = f"#{for_attr}" if for_attr else ""
                    custom.append({"label": label_text, "selector": selector})

        return custom


async def _fill_select(select_el, value: str):
    """Try to select an option matching the value in a <select> element."""
    options = await select_el.query_selector_all("option")
    value_lower = value.lower()

    for option in options:
        text = (await option.inner_text()).strip().lower()
        opt_value = (await option.get_attribute("value") or "").lower()

        if value_lower in text or value_lower in opt_value or text in value_lower:
            actual_value = await option.get_attribute("value")
            await select_el.select_option(value=actual_value)
            return

    # Fallback: try direct select_option
    try:
        await select_el.select_option(label=value)
    except Exception:
        pass


def _is_greenhouse_url(url: str) -> bool:
    """Check if a URL belongs to Greenhouse."""
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    return (
        "greenhouse.io" in hostname
        or "boards.greenhouse.io" in hostname
        or "grnh.se" in hostname
    )
