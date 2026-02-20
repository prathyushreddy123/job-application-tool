import json
import logging
from pathlib import Path

from backend.models.job import FilledField, Job, JobStatus

logger = logging.getLogger(__name__)


def load_mock_jobs(data_dir: Path) -> list[Job]:
    """Load mock jobs from mock-jobs.json for demo mode."""
    path = data_dir / "mock-jobs.json"
    if not path.exists():
        logger.warning(f"Mock jobs file not found: {path}")
        return []

    with open(path) as f:
        raw = json.load(f)

    jobs = []
    for item in raw:
        job = Job(**item)
        # Pre-populate with demo filled fields so cards have data to show
        job.fields = _demo_fields()
        job.status = JobStatus.READY
        jobs.append(job)

    logger.info(f"Loaded {len(jobs)} mock jobs for demo mode")
    return jobs


def _demo_fields() -> list[FilledField]:
    """Generate sample filled fields for demo cards."""
    return [
        FilledField(label="First Name", value="Alex", status="filled", source="personal.first_name"),
        FilledField(label="Last Name", value="Johnson", status="filled", source="personal.last_name"),
        FilledField(label="Email", value="alex.johnson@email.com", status="filled", source="personal.email"),
        FilledField(label="Phone", value="+1-555-123-4567", status="filled", source="personal.phone"),
        FilledField(label="LinkedIn", value="https://linkedin.com/in/alexjohnson", status="filled", source="professional.linkedin_url"),
        FilledField(label="Years Experience", value="5", status="filled", source="professional.years_experience"),
        FilledField(label="Sponsorship Required", value="No", status="filled", source="work_authorization.sponsorship_required"),
        FilledField(label="Salary Expectation", value="", status="skipped", source=""),
        FilledField(label="Why do you want to work here?", value="I am passionate about building impactful products...", status="ai_generated", source="gemini"),
        FilledField(label="Resume", value="resume_2026.pdf", status="filled", source="file"),
    ]
