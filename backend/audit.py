import json
from datetime import datetime, timezone
from pathlib import Path

from backend.models.job import Job


def write_audit_log(job: Job, data_dir: Path) -> Path:
    """Write an audit log entry for a job application attempt."""
    audit_dir = data_dir / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    safe_company = job.company.lower().replace(" ", "_")[:20]
    filename = f"{timestamp}_{safe_company}_{job.id[:8]}.json"

    entry = {
        "timestamp": timestamp,
        "job_id": job.id,
        "job_url": job.job_url,
        "company": job.company,
        "job_title": job.job_title,
        "adapter": job.portal_type,
        "status": job.status.value,
        "fields_filled": {
            f.label: f.value
            for f in job.fields
            if f.status == "filled"
        },
        "fields_skipped": [
            f.label for f in job.fields if f.status == "skipped"
        ],
        "fields_ai_generated": [
            f.label for f in job.fields if f.status == "ai_generated"
        ],
        "screenshot": job.screenshot_path,
        "timing": job.timing.model_dump(),
    }

    path = audit_dir / filename
    with open(path, "w") as f:
        json.dump(entry, f, indent=2)

    return path


def list_audit_logs(data_dir: Path) -> list[dict]:
    """Read all audit log JSON files, sorted newest first."""
    audit_dir = data_dir / "audit"
    if not audit_dir.exists():
        return []

    logs = []
    for path in sorted(audit_dir.glob("*.json"), reverse=True):
        with open(path) as f:
            logs.append(json.load(f))

    return logs
