import logging
from pathlib import Path
from urllib.parse import urlparse

from backend.models.job import FilledField
from backend.profile import get_answer
from backend.automation.adapters.base import BaseAdapter
from backend.automation.adapters.greenhouse import match_label_to_dotpath, LABEL_MAP

logger = logging.getLogger(__name__)

# Workday data-automation-id values -> answers.json dotpath
FIELD_MAP: dict[str, str] = {
    "firstName": "personal.first_name",
    "lastName": "personal.last_name",
    "email": "personal.email",
    "phone-number": "personal.phone",
    "addressLine1": "personal.address.street",
    "city": "personal.address.city",
    "postalCode": "personal.address.zip",
    "currentEmployer": "professional.current_company",
    "jobTitle": "professional.current_title",
}

# Workday-specific label overrides + shared core
WORKDAY_LABEL_MAP: dict[str, str] = {
    **LABEL_MAP,
    "legal first name": "personal.first_name",
    "legal last name": "personal.last_name",
    "preferred first name": "personal.first_name",
    "address line 1": "personal.address.street",
    "postal code": "personal.address.zip",
}


class WorkdayAdapter(BaseAdapter):
    """Adapter for Workday ATS job application forms."""

    name = "workday"

    async def detect(self, page) -> bool:
        """Detect if the current page is a Workday application."""
        url = page.url
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()

        if "myworkdayjobs.com" in hostname or "myworkday.com" in hostname:
            return True

        # Check for Workday DOM markers
        try:
            marker = await page.query_selector(
                '[data-automation-id="applicationContent"], '
                '[data-automation-id="jobPostingPage"]'
            )
            if marker is not None:
                return True

            # Check for Workday iframes
            iframe = await page.query_selector(
                'iframe[src*="myworkday"], iframe[src*="workday"]'
            )
            return iframe is not None
        except Exception:
            return False

    def get_field_map(self) -> dict[str, str]:
        return FIELD_MAP

    async def _get_workday_frame(self, page):
        """Get the Workday iframe content frame, or the page itself."""
        iframe = await page.query_selector(
            'iframe[src*="myworkday"], iframe[src*="workday"]'
        )
        if iframe:
            try:
                frame = await iframe.content_frame()
                if frame:
                    return frame
            except Exception as e:
                logger.warning(f"Failed to access Workday iframe: {e}")
        return page

    async def _fill_workday_dropdown(self, page, automation_id: str, value: str):
        """Fill a Workday custom dropdown (Angular component, not native select)."""
        try:
            # Click the dropdown to open it
            dropdown = await page.query_selector(
                f'[data-automation-id="{automation_id}"] button, '
                f'[data-automation-id="{automation_id}"]'
            )
            if dropdown is None:
                return False

            await dropdown.click()
            await page.wait_for_timeout(500)

            # Look for matching option in the dropdown list
            options = await page.query_selector_all(
                '[data-automation-id="promptOption"], '
                '[role="option"], '
                'li[role="menuitemradio"]'
            )
            value_lower = value.lower()
            for option in options:
                text = (await option.inner_text()).strip().lower()
                if value_lower in text or text in value_lower:
                    await option.click()
                    await page.wait_for_timeout(300)
                    return True

            # Close dropdown if no match
            await page.keyboard.press("Escape")
            return False
        except Exception as e:
            logger.warning(f"Failed to fill Workday dropdown {automation_id}: {e}")
            return False

    async def upload_resume(self, page, resume_path: Path) -> FilledField | None:
        """Upload resume to the Workday file input."""
        if not resume_path.exists():
            logger.warning(f"Resume not found at {resume_path}")
            return FilledField(
                label="Resume", value="", status="failed",
                source=str(resume_path),
            )

        frame = await self._get_workday_frame(page)

        selectors = [
            '[data-automation-id="file-upload-input-ref"]',
            'input[type="file"][data-automation-id*="upload"]',
            'input[type="file"][name*="resume"]',
            'input[type="file"][accept*=".pdf"]',
            'input[type="file"]',
        ]

        for selector in selectors:
            file_input = await frame.query_selector(selector)
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
        """Fill Workday form fields using data-automation-id selectors."""
        results: list[FilledField] = []
        frame = await self._get_workday_frame(page)

        # Fill fields by data-automation-id (FIELD_MAP)
        for auto_id, dotpath in FIELD_MAP.items():
            value = get_answer(profile, dotpath)
            if value is None:
                continue

            # Workday uses data-automation-id on wrapper, input is inside
            selector = (
                f'[data-automation-id="{auto_id}"] input, '
                f'[data-automation-id="{auto_id}"] textarea, '
                f'input[data-automation-id="{auto_id}"], '
                f'textarea[data-automation-id="{auto_id}"]'
            )
            element = await frame.query_selector(selector)

            if element is not None:
                try:
                    await element.fill(value)
                    results.append(FilledField(
                        label=auto_id, value=value,
                        status="filled", source=dotpath,
                    ))
                except Exception as e:
                    logger.warning(f"Failed to fill {auto_id}: {e}")
                    results.append(FilledField(
                        label=auto_id, value="",
                        status="failed", source=dotpath,
                    ))

        # Fallback: fill by label text (WORKDAY_LABEL_MAP)
        labels = await frame.query_selector_all("label")
        for label_el in labels:
            label_text = (await label_el.inner_text()).strip()
            normalized = label_text.lower().strip().rstrip(":").rstrip("*").strip()

            dotpath = WORKDAY_LABEL_MAP.get(normalized)
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
                input_el = await frame.query_selector(f"#{for_attr}")
            else:
                input_el = await label_el.query_selector("input, textarea")

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
        """Navigate Workday multi-step forms.

        Workday SPAs poll continuously, so we use wait_for_timeout
        instead of wait_for_load_state("networkidle").
        """
        page_count = 1
        frame = await self._get_workday_frame(page)

        while True:
            next_btn = await frame.query_selector(
                '[data-automation-id="bottom-navigation-next-button"], '
                'button:has-text("Next"), '
                'button:has-text("Continue")'
            )
            if next_btn is None:
                break

            try:
                await next_btn.click()
                # Workday SPA polls continuously — networkidle never fires
                await page.wait_for_timeout(2000)
                page_count += 1
            except Exception as e:
                logger.warning(f"Failed to navigate to next page: {e}")
                break

        return page_count

    async def submit(self, page) -> bool:
        """Click the Workday submit/done button."""
        try:
            frame = await self._get_workday_frame(page)
            submit_btn = await frame.query_selector(
                '[data-automation-id="bottom-navigation-done-button"], '
                'button:has-text("Submit"), '
                'button[type="submit"]'
            )
            if submit_btn is None:
                logger.error("Submit button not found")
                return False

            await submit_btn.click()
            await page.wait_for_timeout(3000)
            return True
        except Exception as e:
            logger.error(f"Submit failed: {e}")
            return False

    async def detect_custom_questions(self, page) -> list[dict]:
        """Find custom questions on Workday forms."""
        custom = []
        frame = await self._get_workday_frame(page)
        labels = await frame.query_selector_all("label")

        for label_el in labels:
            label_text = (await label_el.inner_text()).strip()
            if not label_text or len(label_text) < 5:
                continue

            normalized = label_text.lower().strip().rstrip(":").rstrip("*").strip()
            if normalized in WORKDAY_LABEL_MAP:
                continue
            if match_label_to_dotpath(label_text) is not None:
                continue

            for_attr = await label_el.get_attribute("for")
            if for_attr:
                input_el = await frame.query_selector(f"#{for_attr}")
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
