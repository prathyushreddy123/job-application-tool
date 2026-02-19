import json
from pathlib import Path

from backend.stats import get_stats


def _write_log(audit_dir: Path, job_id: str, status: str, skipped: list[str] | None = None, ai: list[str] | None = None):
    audit_dir.mkdir(parents=True, exist_ok=True)
    entry = {
        "job_id": job_id,
        "status": status,
        "fields_skipped": skipped or [],
        "fields_ai_generated": ai or [],
    }
    path = audit_dir / f"{job_id}.json"
    path.write_text(json.dumps(entry))


def test_get_stats_empty(tmp_path: Path):
    stats = get_stats(tmp_path)
    assert stats["total"] == 0
    assert stats["success_rate"] == 0.0


def test_get_stats_with_logs(tmp_path: Path):
    _write_log(tmp_path / "audit", "j1", "submitted", skipped=["salary"])
    _write_log(tmp_path / "audit", "j2", "submitted", ai=["why_interested"])
    _write_log(tmp_path / "audit", "j3", "failed", skipped=["salary", "cover_letter"])

    stats = get_stats(tmp_path)
    assert stats["total"] == 3
    assert stats["by_status"]["submitted"] == 2
    assert stats["by_status"]["failed"] == 1
    assert stats["success_rate"] == 66.7
    assert stats["ai_generated_count"] == 1
    assert stats["top_skipped_fields"][0] == ("salary", 2)
