import logging

from fastapi import APIRouter, Depends

from backend.auth import verify_api_key
from backend.models.job import JobStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/automation", dependencies=[Depends(verify_api_key)])


@router.post("/start")
async def start_automation(demo: bool = False, dry_run: bool = False):
    """Start batch processing. Use ?demo=true for demo mode."""
    from backend.main import app_state

    if demo:
        app_state.settings.demo = True
    if dry_run:
        app_state.settings.dry_run = True

    if app_state.settings.demo:
        # Load mock jobs
        from backend.demo import load_mock_jobs

        mock_jobs = load_mock_jobs(app_state.settings.data_dir)
        app_state.job_store.add_jobs(mock_jobs)

        await app_state.ws_manager.broadcast({
            "type": "automation_started",
            "mode": "demo",
            "job_count": len(mock_jobs),
        })
        return {
            "status": "started",
            "mode": "demo",
            "job_count": len(mock_jobs),
        }

    # Real mode: start the pipeline
    ready_jobs = app_state.job_store.get_by_status(JobStatus.NEW)
    if not ready_jobs:
        return {"status": "no_jobs", "message": "No new jobs to process"}

    await app_state.pipeline.start()
    await app_state.pipeline.enqueue(ready_jobs)

    await app_state.ws_manager.broadcast({
        "type": "automation_started",
        "mode": "dry_run" if dry_run else "live",
        "job_count": len(ready_jobs),
    })

    return {
        "status": "started",
        "mode": "dry_run" if dry_run else "live",
        "job_count": len(ready_jobs),
    }


@router.post("/stop")
async def stop_automation():
    """Panic stop — halt all automation immediately."""
    from backend.main import app_state

    if not app_state.settings.demo:
        await app_state.pipeline.stop()

    await app_state.ws_manager.broadcast({"type": "automation_stopped"})
    logger.info("Automation stopped by user")

    return {"status": "stopped"}


@router.get("/status")
async def get_automation_status():
    """Get current pipeline status."""
    from backend.main import app_state

    if app_state.settings.demo:
        store_counts = app_state.job_store.count_by_status()
        return {
            "running": True,
            "mode": "demo",
            "jobs": store_counts,
            "n8n_online": app_state.n8n_client.is_online,
            "n8n_queued": app_state.n8n_client.queued_count,
        }

    pipeline_status = app_state.pipeline.status
    return {
        **pipeline_status,
        "mode": "dry_run" if app_state.settings.dry_run else "live",
        "jobs": app_state.job_store.count_by_status(),
        "n8n_online": app_state.n8n_client.is_online,
        "n8n_queued": app_state.n8n_client.queued_count,
    }
