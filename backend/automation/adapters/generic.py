import logging
from pathlib import Path

from backend.models.job import FilledField
from backend.profile import get_answer
from backend.automation.adapters.base import BaseAdapter

logger = logging.getLogger(__name__)

# No known field names for generic sites
FIELD_MAP: dict[str, str] = {}

# Broad superset of label text -> answers.json dotpath
LABEL_MAP: dict[str, str] = {
    # Name variants
    "full name": "personal.full_name",
    "name": "personal.full_name",
    "your name": "personal.full_name",
    "first name": "personal.first_name",
    "last name": "personal.last_name",
    "given name": "personal.first_name",
    "surname": "personal.last_name",
    "family name": "personal.last_name",
    # Contact
    "email": "personal.email",
    "email address": "personal.email",
    "e-mail": "personal.email",
    "phone": "personal.phone",
    "phone number": "personal.phone",
    "telephone": "personal.phone",
    "mobile": "personal.phone",
    "mobile number": "personal.phone",
    "cell phone": "personal.phone",
    "contact number": "personal.phone",
    # Address
    "city": "personal.address.city",
    "state": "personal.address.state",
    "zip": "personal.address.zip",
    "zip code": "personal.address.zip",
    "postal code": "personal.address.zip",
    "street address": "personal.address.street",
    "address": "personal.address.street",
    "country": "personal.address.country",
    "location": "personal.address.city",
    # Professional
    "linkedin": "professional.linkedin_url",
    "linkedin url": "professional.linkedin_url",
    "linkedin profile": "professional.linkedin_url",
    "portfolio": "professional.portfolio_url",
    "portfolio url": "professional.portfolio_url",
    "website": "professional.portfolio_url",
    "website url": "professional.portfolio_url",
    "github": "professional.github_url",
    "github url": "professional.github_url",
    "current company": "professional.current_company",
    "current employer": "professional.current_company",
    "company": "professional.current_company",
    "organization": "professional.current_company",
    "current title": "professional.current_title",
    "job title": "professional.current_title",
    "title": "professional.current_title",
    "years of experience": "professional.years_experience",
    "years experience": "professional.years_experience",
    "experience": "professional.years_experience",
    # Education
    "degree": "education.0.degree",
    "university": "education.0.school",
    "school": "education.0.school",
    "college": "education.0.school",
    "major": "education.0.major",
    "field of study": "education.0.major",
    "graduation year": "education.0.graduation_year",
    # Work authorization
    "authorized to work": "work_authorization.authorized_us",
    "work authorization": "work_authorization.authorized_us",
    "sponsorship": "work_authorization.sponsorship_required",
    "require sponsorship": "work_authorization.sponsorship_required",
    "visa sponsorship": "work_authorization.sponsorship_required",
    # Demographics
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
    # Cover letter
    "cover letter": "professional.cover_letter",
    "additional information": "professional.additional_info",
}


def _match_generic_label(label: str) -> str | None:
    """Match a label to a dotpath using the generic LABEL_MAP."""
    normalized = label.lower().strip().rstrip(":").rstrip("*").strip()

    if normalized in LABEL_MAP:
        return LABEL_MAP[normalized]

    # Substring match: longest matching key
    best_match = None
    best_len = 0
    for key, dotpath in LABEL_MAP.items():
        if key in normalized and len(key) > best_len:
            best_match = dotpath
            best_len = len(key)

    return best_match


class GenericAdapter(BaseAdapter):
    """Fallback adapter for unknown ATS / direct company career pages."""

    name = "generic"

    async def detect(self, page) -> bool:
        """Always returns True — this is the fallback adapter."""
        return True

    def get_field_map(self) -> dict[str, str]:
        return FIELD_MAP

    async def upload_resume(self, page, resume_path: Path) -> FilledField | None:
        """Upload resume using broad file input selectors."""
        if not resume_path.exists():
            logger.warning(f"Resume not found at {resume_path}")
            return FilledField(
                label="Resume", value="", status="failed",
                source=str(resume_path),
            )

        selectors = [
            'input[type="file"][name*="resume"]',
            'input[type="file"][name*="Resume"]',
            'input[type="file"][name*="cv"]',
            'input[type="file"][name*="CV"]',
            'input[type="file"][accept*=".pdf"]',
            'input[type="file"]',
        ]

        for selector in selectors:
            file_input = await page.query_selector(selector)
            if file_input:
                try:
                    await file_input.set_input_files(str(resume_path))
                    logger.info(f"Resume uploaded: {resume_path.name}")
                    return FilledField(
                        label="Resume", value=resume_path.name,
                        status="filled", source="data/resume.pdf",
                    )
                except Exception as e:
                    logger.warning(f"Resume upload failed with {selector}: {e}")
                    continue

        logger.warning("No file input found for resume upload")
        return FilledField(
            label="Resume", value="", status="skipped", source="",
        )

    async def fill_form(self, page, profile: dict) -> list[FilledField]:
        """Fill form fields using 3-strategy approach."""
        results: list[FilledField] = []
        filled_dotpaths: set[str] = set()

        # Strategy 1: Match by placeholder text
        for selector_type in ["input[placeholder]", "textarea[placeholder]"]:
            elements = await page.query_selector_all(selector_type)
            for el in elements:
                placeholder = (await el.get_attribute("placeholder") or "").strip()
                if not placeholder:
                    continue

                dotpath = _match_generic_label(placeholder)
                if dotpath is None or dotpath in filled_dotpaths:
                    continue

                value = get_answer(profile, dotpath)
                if value is None:
                    continue

                try:
                    await el.fill(value)
                    results.append(FilledField(
                        label=placeholder, value=value,
                        status="filled", source=dotpath,
                    ))
                    filled_dotpaths.add(dotpath)
                except Exception as e:
                    logger.warning(f"Failed to fill placeholder '{placeholder}': {e}")

        # Strategy 2: Match by aria-label
        for selector_type in ["input[aria-label]", "textarea[aria-label]"]:
            elements = await page.query_selector_all(selector_type)
            for el in elements:
                aria_label = (await el.get_attribute("aria-label") or "").strip()
                if not aria_label:
                    continue

                dotpath = _match_generic_label(aria_label)
                if dotpath is None or dotpath in filled_dotpaths:
                    continue

                value = get_answer(profile, dotpath)
                if value is None:
                    continue

                try:
                    await el.fill(value)
                    results.append(FilledField(
                        label=aria_label, value=value,
                        status="filled", source=dotpath,
                    ))
                    filled_dotpaths.add(dotpath)
                except Exception as e:
                    logger.warning(f"Failed to fill aria-label '{aria_label}': {e}")

        # Strategy 3: Match by <label> elements (for/descendant pattern)
        labels = await page.query_selector_all("label")
        for label_el in labels:
            label_text = (await label_el.inner_text()).strip()
            dotpath = _match_generic_label(label_text)
            if dotpath is None or dotpath in filled_dotpaths:
                continue

            value = get_answer(profile, dotpath)
            if value is None:
                continue

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
                        label=label_text, value=value,
                        status="filled", source=dotpath,
                    ))
                    filled_dotpaths.add(dotpath)
                except Exception as e:
                    logger.warning(f"Failed to fill '{label_text}': {e}")
                    results.append(FilledField(
                        label=label_text, value="",
                        status="failed", source=dotpath,
                    ))

        return results

    async def navigate_pages(self, page) -> int:
        """Click Next/Continue buttons, with a max 10 page cap."""
        page_count = 1
        max_pages = 10

        while page_count < max_pages:
            next_btn = await page.query_selector(
                'button:has-text("Next"), '
                'button:has-text("Continue"), '
                'input[type="submit"][value*="Next"], '
                'input[type="submit"][value*="Continue"], '
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
        """Click the submit button using broad selectors."""
        try:
            submit_btn = await page.query_selector(
                'button[type="submit"], '
                'button:has-text("Submit"), '
                'button:has-text("Apply"), '
                'button:has-text("Send Application"), '
                'input[type="submit"]'
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
        """Find custom free-text questions by scanning all labels."""
        custom = []
        labels = await page.query_selector_all("label")

        for label_el in labels:
            label_text = (await label_el.inner_text()).strip()
            if not label_text or len(label_text) < 5:
                continue

            if _match_generic_label(label_text) is not None:
                continue

            for_attr = await label_el.get_attribute("for")
            if for_attr:
                input_el = await page.query_selector(f"#{for_attr}")
            else:
                input_el = await label_el.query_selector(
                    "textarea, input[type='text']"
                )

            if input_el is not None:
                tag = await input_el.evaluate("el => el.tagName.toLowerCase()")
                if tag in ("textarea", "input"):
                    selector = f"#{for_attr}" if for_attr else ""
                    custom.append({"label": label_text, "selector": selector})

        return custom


async def _fill_select(select_el, value: str):
    """Try to select an option matching the value."""
    options = await select_el.query_selector_all("option")
    value_lower = value.lower()

    for option in options:
        text = (await option.inner_text()).strip().lower()
        opt_value = (await option.get_attribute("value") or "").lower()

        if value_lower in text or value_lower in opt_value or text in value_lower:
            actual_value = await option.get_attribute("value")
            await select_el.select_option(value=actual_value)
            return

    try:
        await select_el.select_option(label=value)
    except Exception:
        pass
