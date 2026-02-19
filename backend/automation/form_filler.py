import asyncio
import logging
from datetime import datetime, timezone

from backend.automation.adapters.base import BaseAdapter
from backend.automation.ats_detect import detect_ats_type, get_adapter
from backend.automation.browser import BrowserManager
from backend.automation.rate_limiter import RateLimiter
from backend.config import Settings
from backend.models.job import FilledField, Job, JobStatus
from backend.profile import get_answer, load_profile, search_answer_bank

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class FormFillingPipeline:
    """Orchestrates the fill-ahead pipeline for batch job processing.

    Maintains a buffer of pre-filled forms so the user can review cards
    without waiting for each form to load. Forms are re-filled fresh
    on approval to guarantee data freshness.
    """

    def __init__(
        self,
        browser: BrowserManager,
        settings: Settings,
        rate_limiter: RateLimiter,
    ):
        self._browser = browser
        self._settings = settings
        self._rate_limiter = rate_limiter
        self._profile: dict = {}

        # Job queues
        self._pending: asyncio.Queue[Job] = asyncio.Queue()
        self._ready: list[Job] = []  # Pre-filled, awaiting review
        self._buffer_task: asyncio.Task | None = None
        self._running = False

        # Tracking
        self._consecutive_failures = 0
        self._total_processed = 0

    async def start(self):
        """Start the pipeline: load profile and begin fill-ahead loop."""
        self._profile = load_profile(self._settings.data_dir)
        self._running = True
        self._buffer_task = asyncio.create_task(self._maintain_buffer())
        logger.info("Form filling pipeline started")

    async def stop(self):
        """Stop the pipeline gracefully."""
        self._running = False
        if self._buffer_task is not None:
            self._buffer_task.cancel()
            try:
                await self._buffer_task
            except asyncio.CancelledError:
                pass
            self._buffer_task = None
        logger.info("Form filling pipeline stopped")

    async def enqueue(self, jobs: list[Job]):
        """Add jobs to the pending queue for processing."""
        for job in jobs:
            await self._pending.put(job)
        logger.info(f"Enqueued {len(jobs)} jobs (queue size: {self._pending.qsize()})")

    async def get_ready_job(self) -> Job | None:
        """Pop the next pre-filled job ready for review. Returns None if empty."""
        if self._ready:
            return self._ready.pop(0)
        return None

    async def fill_single(self, job: Job) -> Job:
        """Fill a single job's application form.

        Opens the URL, detects ATS, runs the adapter, takes screenshot.
        Returns the updated Job with fields and screenshot populated.
        """
        job.status = JobStatus.FILLING
        job.timing.url_opened_at = _now_iso()
        page = None

        try:
            # Rate limit check
            await self._rate_limiter.wait_if_needed(job.job_url)

            page = await self._browser.new_page()
            await page.goto(job.job_url, wait_until="networkidle", timeout=30000)
            await self._browser.random_delay()

            # Detect ATS type if not already set
            if not job.portal_type:
                job.portal_type = detect_ats_type(job.job_url)

            # Get adapter
            adapter = get_adapter(job.portal_type)
            if adapter is None:
                logger.warning(f"No adapter for {job.portal_type}, skipping")
                job.status = JobStatus.FAILED
                job.error_log = f"No adapter available for ATS type: {job.portal_type}"
                return job

            # Verify adapter can handle this page
            if not await adapter.detect(page):
                logger.warning(f"Adapter {adapter.name} cannot handle {job.job_url}")
                job.status = JobStatus.FAILED
                job.error_log = f"Adapter detection failed for {job.job_url}"
                return job

            # Fill the form
            fields = await adapter.fill_form(page, self._profile)

            # Handle custom questions (answer bank search)
            custom_questions = await adapter.detect_custom_questions(page)
            for cq in custom_questions:
                answer = search_answer_bank(self._profile, cq["label"])
                if answer:
                    # Try to fill the custom field
                    if cq["selector"]:
                        try:
                            el = await page.query_selector(cq["selector"])
                            if el:
                                await el.fill(answer)
                                fields.append(FilledField(
                                    label=cq["label"],
                                    value=answer,
                                    status="filled",
                                    source="answer_bank",
                                ))
                        except Exception:
                            fields.append(FilledField(
                                label=cq["label"],
                                value="",
                                status="skipped",
                                source="",
                            ))
                else:
                    # Mark as skipped (Gemini fallback will be added in Phase 5)
                    fields.append(FilledField(
                        label=cq["label"],
                        value="",
                        status="skipped",
                        source="",
                    ))

            # Navigate multi-page forms
            page_count = await adapter.navigate_pages(page)
            if page_count > 1:
                # Re-fill fields on new pages
                extra_fields = await adapter.fill_form(page, self._profile)
                fields.extend(extra_fields)

            job.fields = fields
            job.timing.form_filled_at = _now_iso()

            # Take screenshot of the final page
            screenshot_dir = self._settings.data_dir / "screenshots"
            screenshot_path = str(screenshot_dir / f"{job.id}.png")
            await self._browser.screenshot(page, screenshot_path)
            job.screenshot_path = screenshot_path

            job.status = JobStatus.READY
            self._consecutive_failures = 0
            logger.info(
                f"Filled {job.company} - {job.job_title} "
                f"({len([f for f in fields if f.status == 'filled'])} fields filled)"
            )

        except Exception as e:
            logger.error(f"Failed to fill {job.company}: {e}")
            job.status = JobStatus.FAILED
            job.error_log = str(e)
            self._consecutive_failures += 1
        finally:
            if page is not None:
                await self._browser.close_page(page)
            self._total_processed += 1

        return job

    async def refill_and_submit(self, job: Job, dry_run: bool = False) -> Job:
        """Re-fill a form fresh and submit it.

        Called when the user approves a card. Re-fills to guarantee
        freshness, then submits (unless dry_run). Retries once on failure,
        then pauses for manual intervention.
        """
        job.status = JobStatus.APPROVED
        job.timing.user_reviewed_at = _now_iso()

        for attempt in range(2):  # Max 2 attempts (initial + 1 retry)
            page = None
            try:
                await self._rate_limiter.wait_if_needed(job.job_url)
                self._rate_limiter.record(job.job_url)

                page = await self._browser.new_page()
                await page.goto(job.job_url, wait_until="networkidle", timeout=30000)
                await self._browser.random_delay()

                adapter = get_adapter(job.portal_type)
                if adapter is None:
                    job.status = JobStatus.FAILED
                    job.error_log = f"No adapter for {job.portal_type}"
                    return job

                # Re-fill the form
                fields = await adapter.fill_form(page, self._profile)

                # Navigate multi-page forms
                page_count = await adapter.navigate_pages(page)
                if page_count > 1:
                    extra_fields = await adapter.fill_form(page, self._profile)
                    fields.extend(extra_fields)

                job.fields = fields

                # Take final screenshot before submission
                screenshot_dir = self._settings.data_dir / "screenshots"
                screenshot_path = str(screenshot_dir / f"{job.id}_final.png")
                await self._browser.screenshot(page, screenshot_path)
                job.screenshot_path = screenshot_path

                if dry_run:
                    logger.info(f"DRY RUN: Would submit {job.company} - {job.job_title}")
                    job.status = JobStatus.SUBMITTED
                    job.timing.submitted_at = _now_iso()
                    return job

                # Submit
                success = await adapter.submit(page)
                if success:
                    job.status = JobStatus.SUBMITTED
                    job.timing.submitted_at = _now_iso()
                    logger.info(f"Submitted: {job.company} - {job.job_title}")
                    return job
                else:
                    raise RuntimeError("Submit button click returned False")

            except Exception as e:
                logger.warning(
                    f"Attempt {attempt + 1} failed for {job.company}: {e}"
                )
                if attempt == 0:
                    logger.info("Retrying once...")
                    if page:
                        await self._browser.close_page(page)
                        page = None
                    await asyncio.sleep(2)
                    continue

                # Second attempt failed -> pause for manual intervention
                job.status = JobStatus.FAILED
                job.error_log = f"Failed after retry: {e}"
                self._consecutive_failures += 1

                # Bring browser to front for manual intervention
                if page:
                    await self._browser.bring_to_front(page)
                    logger.info(
                        "Paused for manual intervention. "
                        "Browser brought to front."
                    )
                    # Don't close the page — user needs to interact
                    return job
            finally:
                if page and job.status in (JobStatus.SUBMITTED, JobStatus.FAILED):
                    # Only close if we're done (not paused for intervention)
                    if job.error_log and "Failed after retry" not in job.error_log:
                        await self._browser.close_page(page)
                    elif job.status == JobStatus.SUBMITTED:
                        await self._browser.close_page(page)

        return job

    async def _maintain_buffer(self):
        """Background task that keeps the fill-ahead buffer at capacity."""
        buffer_size = self._settings.fill_ahead_buffer

        while self._running:
            try:
                # Fill buffer up to capacity
                while (
                    len(self._ready) < buffer_size
                    and not self._pending.empty()
                    and self._consecutive_failures < 3
                ):
                    job = await asyncio.wait_for(
                        self._pending.get(), timeout=1.0
                    )
                    filled_job = await self.fill_single(job)
                    if filled_job.status == JobStatus.READY:
                        self._ready.append(filled_job)

                # Auto-stop on 3 consecutive failures
                if self._consecutive_failures >= 3:
                    logger.error(
                        "3 consecutive failures. Pipeline auto-stopped."
                    )
                    self._running = False
                    break

                # Wait before checking again
                await asyncio.sleep(1.0)

            except asyncio.TimeoutError:
                await asyncio.sleep(0.5)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Buffer maintenance error: {e}")
                await asyncio.sleep(2.0)

    @property
    def status(self) -> dict:
        """Return current pipeline status."""
        return {
            "running": self._running,
            "pending_count": self._pending.qsize(),
            "ready_count": len(self._ready),
            "total_processed": self._total_processed,
            "consecutive_failures": self._consecutive_failures,
            "rate_limits": self._rate_limiter.get_status(),
        }

    @property
    def is_queue_empty(self) -> bool:
        return self._pending.empty() and len(self._ready) == 0
