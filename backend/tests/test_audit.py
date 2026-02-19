import json
from pathlib import Path

from backend.audit import list_audit_logs, write_audit_log
from backend.models.job import FilledField, Job, JobStatus, JobTiming


def _make_job(**overrides) -> Job:
    defaults = {
        "id": "test-uuid-1234",
        "job_url": "https://boards.greenhouse.io/test/jobs/1",
        "company": "TestCorp",
        "job_title": "Engineer",
        "portal_type": "greenhouse",
        "status": JobStatus.SUBMITTED,
        "fields": [
            FilledField(label="first_name", value="Alex", status="filled", source="personal.first_name"),
            FilledField(label="salary", value="", status="skipped", source=""),
            FilledField(label="why_interested", value="AI generated answer", status="ai_generated", source="gemini"),
        ],
        "timing": JobTiming(
            url_opened_at="2026-02-19T10:00:00Z",
            form_filled_at="2026-02-19T10:00:30Z",
            user_reviewed_at="2026-02-19T10:01:00Z",
            submitted_at="2026-02-19T10:01:05Z",
        ),
    }
    defaults.update(overrides)
    return Job(**defaults)


def test_write_audit_log(tmp_path: Path):
    job = _make_job()
    path = write_audit_log(job, tmp_path)

    assert path.exists()
    data = json.loads(path.read_text())

    assert data["job_id"] == "test-uuid-1234"
    assert data["company"] == "TestCorp"
    assert data["status"] == "submitted"
    assert data["fields_filled"]["first_name"] == "Alex"
    assert "salary" in data["fields_skipped"]
    assert "why_interested" in data["fields_ai_generated"]


def test_audit_timing_data(tmp_path: Path):
    job = _make_job()
    path = write_audit_log(job, tmp_path)
    data = json.loads(path.read_text())

    assert data["timing"]["url_opened_at"] == "2026-02-19T10:00:00Z"
    assert data["timing"]["submitted_at"] == "2026-02-19T10:01:05Z"


def test_list_audit_logs(tmp_path: Path):
    job1 = _make_job(id="uuid-1", company="CompanyA")
    job2 = _make_job(id="uuid-2", company="CompanyB")

    write_audit_log(job1, tmp_path)
    write_audit_log(job2, tmp_path)

    logs = list_audit_logs(tmp_path)
    assert len(logs) == 2


def test_list_audit_logs_empty(tmp_path: Path):
    logs = list_audit_logs(tmp_path)
    assert logs == []
