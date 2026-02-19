from collections import Counter
from pathlib import Path

from backend.audit import list_audit_logs


def get_stats(data_dir: Path) -> dict:
    """Aggregate stats from audit logs."""
    logs = list_audit_logs(data_dir)

    if not logs:
        return {
            "total": 0,
            "by_status": {},
            "success_rate": 0.0,
            "top_skipped_fields": [],
            "ai_generated_count": 0,
        }

    status_counts = Counter(log.get("status", "unknown") for log in logs)
    total = len(logs)
    submitted = status_counts.get("submitted", 0)

    skipped_fields: Counter[str] = Counter()
    ai_count = 0
    for log in logs:
        for field in log.get("fields_skipped", []):
            skipped_fields[field] += 1
        ai_count += len(log.get("fields_ai_generated", []))

    return {
        "total": total,
        "by_status": dict(status_counts),
        "success_rate": round(submitted / total * 100, 1) if total else 0.0,
        "top_skipped_fields": skipped_fields.most_common(10),
        "ai_generated_count": ai_count,
    }
