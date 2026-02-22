import logging
from pathlib import Path
from urllib.parse import urlparse

from backend.models.job import FilledField
from backend.profile import get_answer
from backend.automation.adapters.base import BaseAdapter
from backend.automation.adapters.greenhouse import match_label_to_dotpath, LABEL_MAP

logger = logging.getLogger(__name__)

# Lever form field name/id -> answers.json dotpath
FIELD_MAP: dict[str, str] = {
    "name": "personal.full_name",
    "email": "personal.email",
    "phone": "personal.phone",
    "org": "professional.current_company",
    "urls[LinkedIn]": "professional.linkedin_url",
    "urls[GitHub]": "professional.github_url",
    "urls[Portfolio]": "professional.portfolio_url",
    "location": "personal.address.city",
    "comments": "professional.cover_letter",
}

# Lever-specific label overrides + shared core
LEVER_LABEL_MAP: dict[str, str] = {
    **LABEL_MAP,
    "full name": "personal.full_name",
    "name": "personal.full_name",
    "additional information": "professional.additional_info",
    "cover letter": "professional.cover_letter",
    "current company": "professional.current_company",
    "organization": "professional.current_company",
}


class LeverAdapter(BaseAdapter):
    """Adapter for Lever ATS job application forms."""

    name = "lever"

    async def detect(self, page) -> bool:
        """Detect if the current page is a Lever application."""
        url = page.url
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()
        if "lever.co" in hostname:
            return True

        try:
            marker = await page.query_selector(
                "#application-form, .lever-apply-page"
            )
            return marker is not None
        except Exception:
            return False

    def get_field_map(self) -> dict[str, str]:
        return FIELD_MAP

    async def upload_resume(self, page, resume_path: Path) -> FilledField | None:
        """Upload resume to the Lever file input."""
        if not resume_path.exists():
            logger.warning(f"Resume not found at {resume_path}")
            return FilledField(
                label="Resume", value="", status="failed",
                source=str(resume_path),
            )

        selectors = [
            'input[type="file"][name="resume"]',
            'input[type="file"][name*="resume"]',
            'input[type="file"].resume-upload',
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
        """Fill all detectable form fields on the current Lever page."""
        results: list[FilledField] = []

        # Fill fields by name/id attribute (FIELD_MAP)
        for field_name, dotpath in FIELD_MAP.items():
            value = get_answer(profile, dotpath)
            if value is None:
                continue

            selector = f'input[name="{field_name}"], textarea[name="{field_name}"]'
            element = await page.query_selector(selector)
            if element is None:
                selector = f'#{field_name}'
                element = await page.query_selector(selector)

            if element is not None:
                try:
                    await element.fill(value)
                    results.append(FilledField(
                        label=field_name, value=value,
                        status="filled", source=dotpath,
                    ))
                except Exception as e:
                    logger.warning(f"Failed to fill {field_name}: {e}")
                    results.append(FilledField(
                        label=field_name, value="",
                        status="failed", source=dotpath,
                    ))

        # Fill fields by label text (LEVER_LABEL_MAP fallback)
        labels = await page.query_selector_all("label")
        for label_el in labels:
            label_text = (await label_el.inner_text()).strip()
            normalized = label_text.lower().strip().rstrip(":").rstrip("*").strip()

            dotpath = LEVER_LABEL_MAP.get(normalized)
            if dotpath is None:
                dotpath = match_label_to_dotpath(label_text)
            if dotpath is None:
                continue

            if any(f.source == dotpath and f.status == "filled" for f in results):
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
                    await input_el.fill(value)
                    results.append(FilledField(
                        label=label_text, value=value,
                        status="filled", source=dotpath,
                    ))
                except Exception as e:
                    logger.warning(f"Failed to fill '{label_text}': {e}")
                    results.append(FilledField(
                        label=label_text, value="",
                        status="failed", source=dotpath,
                    ))

        return results

    async def navigate_pages(self, page) -> int:
        """Lever forms are single-page — no navigation needed."""
        return 1

    async def submit(self, page) -> bool:
        """Click the Lever submit button."""
        try:
            submit_btn = await page.query_selector(
                'button[type="submit"], '
                'button:has-text("Submit Application"), '
                'button:has-text("Submit")'
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
        """Find custom questions on Lever forms."""
        custom = []

        # Lever wraps custom questions in .application-question divs
        question_divs = await page.query_selector_all(".application-question")
        for div in question_divs:
            label_el = await div.query_selector("label")
            if label_el is None:
                continue

            label_text = (await label_el.inner_text()).strip()
            if not label_text or len(label_text) < 5:
                continue

            normalized = label_text.lower().strip().rstrip(":").rstrip("*").strip()
            if normalized in LEVER_LABEL_MAP:
                continue
            if match_label_to_dotpath(label_text) is not None:
                continue

            input_el = await div.query_selector("textarea, input[type='text']")
            if input_el is not None:
                custom.append({"label": label_text, "selector": ""})

        # Fallback: scan all labels like Greenhouse
        if not question_divs:
            labels = await page.query_selector_all("label")
            for label_el in labels:
                label_text = (await label_el.inner_text()).strip()
                if not label_text or len(label_text) < 5:
                    continue

                if match_label_to_dotpath(label_text) is not None:
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
