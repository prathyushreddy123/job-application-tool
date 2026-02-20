import logging

from fastapi import APIRouter
from pydantic import BaseModel

from backend.automation.ats_detect import detect_ats_type
from backend.models.job import Job

logger = logging.getLogger(__name__)

# No API key auth on webhooks — n8n calls these
router = APIRouter(prefix="/api/webhooks")


class JobSyncPayload(BaseModel):
    jobs: list[dict]


@router.post("/jobs-sync")
async def jobs_sync(payload: JobSyncPayload):
    """Receive new jobs from n8n (synced from Google Sheets)."""
    from backend.main import app_state

    new_jobs = []
    for item in payload.jobs:
        # Auto-detect portal_type if not set
        if not item.get("portal_type"):
            item["portal_type"] = detect_ats_type(item.get("job_url", ""))

        try:
            job = Job(**item)
            new_jobs.append(job)
        except Exception as e:
            logger.warning(f"Invalid job data from n8n: {e} — {item}")

    if new_jobs:
        app_state.job_store.add_jobs(new_jobs)
        await app_state.ws_manager.broadcast({
            "type": "jobs_synced",
            "count": len(new_jobs),
        })

    logger.info(f"Synced {len(new_jobs)} jobs from n8n")
    return {"synced": len(new_jobs)}
