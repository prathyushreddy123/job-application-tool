import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.auth import verify_api_key
from backend.models.job import JobStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/jobs", dependencies=[Depends(verify_api_key)])

# Separate router for endpoints that don't need auth (e.g. <img> tags)
public_router = APIRouter(prefix="/api/jobs")


@router.get("")
async def get_jobs():
    """Get all cached jobs."""
    from backend.main import app_state

    jobs = app_state.job_store.get_all()
    return [job.model_dump() for job in jobs]


@router.post("/{job_id}/approve")
async def approve_job(job_id: str):
    """Approve a job and trigger re-fill + submit."""
    from backend.main import app_state

    job = app_state.job_store.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status not in (JobStatus.READY, JobStatus.NEW):
        raise HTTPException(
            status_code=400,
            detail=f"Job cannot be approved (status: {job.status.value})",
        )

    # In demo mode, just mark as submitted
    if app_state.settings.demo:
        job.status = JobStatus.SUBMITTED
        await app_state.ws_manager.broadcast({
            "type": "job_submitted",
            "job_id": job.id,
            "company": job.company,
        })
        return {"status": "submitted", "job_id": job.id}

    # Real mode: re-fill and submit via pipeline
    dry_run = app_state.settings.dry_run
    result = await app_state.pipeline.refill_and_submit(job, dry_run=dry_run)

    # Write audit log
    from backend.audit import write_audit_log
    write_audit_log(result, app_state.settings.data_dir)

    # Update n8n
    await app_state.n8n_client.update_job_status(
        job_id=result.id,
        status=result.status.value,
        date_applied=result.timing.submitted_at,
        error_log=result.error_log,
    )

    # Broadcast to WebSocket
    if result.status == JobStatus.SUBMITTED:
        await app_state.ws_manager.broadcast({
            "type": "job_submitted",
            "job_id": result.id,
            "company": result.company,
        })
    elif result.status == JobStatus.FAILED:
        await app_state.ws_manager.broadcast({
            "type": "job_failed",
            "job_id": result.id,
            "company": result.company,
            "error": result.error_log,
        })
        await app_state.n8n_client.report_failure(
            job_url=result.job_url,
            company=result.company,
            error=result.error_log,
            failure_count=app_state.pipeline.status["consecutive_failures"],
        )

    return {"status": result.status.value, "job_id": result.id}


@router.post("/{job_id}/skip")
async def skip_job(job_id: str):
    """Skip a job application."""
    from backend.main import app_state

    job = app_state.job_store.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    job.status = JobStatus.SKIPPED

    # Write audit log
    from backend.audit import write_audit_log
    write_audit_log(job, app_state.settings.data_dir)

    # Update n8n
    if not app_state.settings.demo:
        await app_state.n8n_client.update_job_status(
            job_id=job.id,
            status="skipped",
        )

    # Broadcast
    await app_state.ws_manager.broadcast({
        "type": "job_skipped",
        "job_id": job.id,
        "company": job.company,
    })

    return {"status": "skipped", "job_id": job.id}


class FieldEdit(BaseModel):
    label: str
    value: str


class EditRequest(BaseModel):
    fields: list[FieldEdit]
    bring_browser_to_front: bool = False


@router.post("/{job_id}/edit")
async def edit_job(job_id: str, req: EditRequest):
    """Update filled field values and optionally bring browser to front."""
    from backend.main import app_state

    job = app_state.job_store.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    # Apply field edits
    edits_applied = 0
    for edit in req.fields:
        for field in job.fields:
            if field.label == edit.label:
                field.value = edit.value
                field.status = "filled"
                edits_applied += 1
                break

    # Bring browser to front for complex edits
    if req.bring_browser_to_front and app_state.browser.is_running:
        pages = app_state.browser._pages
        if pages:
            await app_state.browser.bring_to_front(pages[-1])

    logger.info(f"Edited {edits_applied} fields on job {job_id}")
    return {"status": "edited", "job_id": job.id, "edits_applied": edits_applied}


# --- Public (no auth) endpoints ---


@public_router.get("/{job_id}/screenshot")
async def get_screenshot(job_id: str):
    """Return the screenshot image for a job.

    No auth required — served as static image for <img> tags.
    """
    from backend.main import app_state

    job = app_state.job_store.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    if not job.screenshot_path:
        raise HTTPException(status_code=404, detail="No screenshot available")

    screenshot_file = Path(job.screenshot_path)
    if not screenshot_file.exists():
        raise HTTPException(status_code=404, detail="Screenshot file not found")

    return FileResponse(job.screenshot_path, media_type="image/png")
