"""Tests for backend/demo.py"""
from pathlib import Path

from backend.demo import load_mock_jobs, _demo_fields


def test_load_mock_jobs():
    jobs = load_mock_jobs(Path("./data"))
    assert len(jobs) == 5
    for job in jobs:
        assert job.status.value == "ready"
        assert len(job.fields) == 10
        assert job.company
        assert job.job_title


def test_load_mock_jobs_missing_file():
    jobs = load_mock_jobs(Path("/nonexistent"))
    assert jobs == []


def test_demo_fields():
    fields = _demo_fields()
    assert len(fields) == 10
    statuses = {f.status for f in fields}
    assert "filled" in statuses
    assert "skipped" in statuses
    assert "ai_generated" in statuses

    # Check specific fields exist
    labels = [f.label for f in fields]
    assert "First Name" in labels
    assert "Email" in labels
    assert "Resume" in labels


def test_demo_fields_ai_generated_has_value():
    fields = _demo_fields()
    ai_fields = [f for f in fields if f.status == "ai_generated"]
    assert len(ai_fields) >= 1
    for f in ai_fields:
        assert f.value  # AI fields should have content


def test_demo_fields_skipped_has_no_value():
    fields = _demo_fields()
    skipped = [f for f in fields if f.status == "skipped"]
    assert len(skipped) >= 1
    for f in skipped:
        assert f.value == ""  # Skipped fields should be empty
