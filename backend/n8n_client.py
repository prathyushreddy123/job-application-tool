import asyncio
import logging
from dataclasses import dataclass, field

import httpx

from backend.config import Settings

logger = logging.getLogger(__name__)


@dataclass
class _QueuedCall:
    """A failed webhook call queued for retry."""
    endpoint: str
    payload: dict
    attempts: int = 0


class N8nClient:
    """HTTP client for communicating with n8n webhooks.

    Handles status updates, failure reports, and notifications.
    Queues failed calls and retries with exponential backoff when
    n8n is offline.
    """

    def __init__(self, settings: Settings):
        self._webhook_url = settings.n8n_webhook_url.rstrip("/")
        self._n8n_url = settings.n8n_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=10.0)
        self._retry_queue: asyncio.Queue[_QueuedCall] = asyncio.Queue()
        self._retry_task: asyncio.Task | None = None
        self._online = False
        self._health_task: asyncio.Task | None = None

    async def start(self):
        """Start background tasks for retry loop and health checks."""
        self._online = await self._check_health()
        self._retry_task = asyncio.create_task(self._retry_loop())
        self._health_task = asyncio.create_task(self._health_check_loop())
        logger.info(f"n8n client started (online={self._online})")

    async def stop(self):
        """Stop background tasks and close HTTP client."""
        if self._retry_task:
            self._retry_task.cancel()
            try:
                await self._retry_task
            except asyncio.CancelledError:
                pass
        if self._health_task:
            self._health_task.cancel()
            try:
                await self._health_task
            except asyncio.CancelledError:
                pass
        await self._client.aclose()
        logger.info(
            f"n8n client stopped "
            f"(queued calls remaining: {self._retry_queue.qsize()})"
        )

    @property
    def is_online(self) -> bool:
        return self._online

    @property
    def queued_count(self) -> int:
        return self._retry_queue.qsize()

    async def update_job_status(
        self,
        job_id: str,
        status: str,
        date_applied: str = "",
        error_log: str = "",
    ):
        """Send a job status update to n8n (which writes to Google Sheets)."""
        payload = {
            "job_id": job_id,
            "status": status,
            "date_applied": date_applied,
            "error_log": error_log,
        }
        await self._post("job-status-update", payload)

    async def report_failure(
        self,
        job_url: str,
        company: str,
        error: str,
        failure_count: int,
    ):
        """Report a job failure to n8n (triggers error notification if 3+)."""
        payload = {
            "job_url": job_url,
            "company": company,
            "error": error,
            "failure_count": failure_count,
        }
        await self._post("job-failed", payload)

    async def _post(self, endpoint: str, payload: dict):
        """POST to an n8n webhook endpoint. Queue for retry on failure."""
        url = f"{self._webhook_url}/{endpoint}"
        try:
            response = await self._client.post(url, json=payload)
            response.raise_for_status()
            logger.debug(f"n8n POST {endpoint}: {response.status_code}")
        except Exception as e:
            logger.warning(
                f"n8n POST {endpoint} failed: {e}. Queuing for retry."
            )
            await self._retry_queue.put(
                _QueuedCall(endpoint=endpoint, payload=payload)
            )

    async def _retry_loop(self):
        """Background task: retry queued calls with exponential backoff."""
        while True:
            try:
                call = await self._retry_queue.get()

                # Exponential backoff: 1s, 2s, 4s, 8s, ... up to 300s (5 min)
                delay = min(2 ** call.attempts, 300)
                await asyncio.sleep(delay)

                url = f"{self._webhook_url}/{call.endpoint}"
                try:
                    response = await self._client.post(url, json=call.payload)
                    response.raise_for_status()
                    logger.info(
                        f"n8n retry succeeded for {call.endpoint} "
                        f"(attempt {call.attempts + 1})"
                    )
                except Exception as e:
                    call.attempts += 1
                    if call.attempts < 10:  # Max 10 retries
                        logger.warning(
                            f"n8n retry failed for {call.endpoint} "
                            f"(attempt {call.attempts}): {e}"
                        )
                        await self._retry_queue.put(call)
                    else:
                        logger.error(
                            f"n8n call permanently failed after "
                            f"{call.attempts} attempts: {call.endpoint}"
                        )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Retry loop error: {e}")
                await asyncio.sleep(5)

    async def _check_health(self) -> bool:
        """Check if n8n is reachable."""
        try:
            response = await self._client.get(
                f"{self._n8n_url}/healthz", timeout=5.0
            )
            return response.status_code == 200
        except Exception:
            return False

    async def _health_check_loop(self):
        """Background task: check n8n health every 30 seconds."""
        while True:
            try:
                was_online = self._online
                self._online = await self._check_health()
                if not was_online and self._online:
                    logger.info("n8n is back online")
                elif was_online and not self._online:
                    logger.warning("n8n went offline")
                await asyncio.sleep(30)
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(30)
