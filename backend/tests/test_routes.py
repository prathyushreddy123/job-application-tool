"""Integration tests for API routes using FastAPI TestClient."""
import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture(scope="module")
def client():
    """TestClient that triggers startup/shutdown events."""
    with TestClient(app) as c:
        yield c


HEADERS = {"X-API-Key": "dev-key"}


class TestHealth:
    def test_health(self, client):
        res = client.get("/health")
        assert res.status_code == 200
        assert res.json() == {"status": "ok"}


class TestAuth:
    def test_missing_key(self, client):
        res = client.get("/api/jobs")
        assert res.status_code == 422  # Missing required header

    def test_wrong_key(self, client):
        res = client.get("/api/jobs", headers={"X-API-Key": "wrong"})
        assert res.status_code == 401

    def test_valid_key(self, client):
        res = client.get("/api/jobs", headers=HEADERS)
        assert res.status_code == 200


class TestJobsBeforeStart:
    def test_empty_jobs(self, client):
        res = client.get("/api/jobs", headers=HEADERS)
        assert res.status_code == 200
        assert res.json() == []

    def test_approve_nonexistent(self, client):
        res = client.post("/api/jobs/no-such-id/approve", headers=HEADERS)
        assert res.status_code == 404

    def test_skip_nonexistent(self, client):
        res = client.post("/api/jobs/no-such-id/skip", headers=HEADERS)
        assert res.status_code == 404


class TestDemoMode:
    def test_start_demo(self, client):
        res = client.post("/api/automation/start?demo=true", headers=HEADERS)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "started"
        assert data["mode"] == "demo"
        assert data["job_count"] == 5

    def test_jobs_loaded(self, client):
        res = client.get("/api/jobs", headers=HEADERS)
        assert res.status_code == 200
        jobs = res.json()
        assert len(jobs) == 5
        for job in jobs:
            assert job["status"] == "ready"
            assert job["portal_type"] == "greenhouse"
            assert len(job["fields"]) == 10

    def test_approve_job(self, client):
        jobs = client.get("/api/jobs", headers=HEADERS).json()
        job_id = jobs[0]["id"]
        res = client.post(f"/api/jobs/{job_id}/approve", headers=HEADERS)
        assert res.status_code == 200
        assert res.json()["status"] == "submitted"

        # Verify status changed
        updated = client.get("/api/jobs", headers=HEADERS).json()
        approved = [j for j in updated if j["id"] == job_id][0]
        assert approved["status"] == "submitted"

    def test_skip_job(self, client):
        jobs = client.get("/api/jobs", headers=HEADERS).json()
        # Find a ready job
        ready = [j for j in jobs if j["status"] == "ready"]
        assert len(ready) > 0
        job_id = ready[0]["id"]

        res = client.post(f"/api/jobs/{job_id}/skip", headers=HEADERS)
        assert res.status_code == 200
        assert res.json()["status"] == "skipped"

    def test_status_running(self, client):
        res = client.get("/api/automation/status", headers=HEADERS)
        assert res.status_code == 200
        data = res.json()
        assert data["running"] is True
        assert data["mode"] == "demo"

    def test_stop(self, client):
        res = client.post("/api/automation/stop", headers=HEADERS)
        assert res.status_code == 200
        assert res.json()["status"] == "stopped"

    def test_status_after_stop(self, client):
        res = client.get("/api/automation/status", headers=HEADERS)
        assert res.status_code == 200
        assert res.json()["running"] is False


class TestWebhook:
    def test_sync_jobs(self, client):
        payload = {
            "jobs": [
                {
                    "id": "test-webhook-001",
                    "job_url": "https://boards.greenhouse.io/test/jobs/99",
                    "company": "WebhookCo",
                    "job_title": "Tester",
                }
            ]
        }
        res = client.post("/api/webhooks/jobs-sync", json=payload)
        assert res.status_code == 200
        assert res.json()["synced"] == 1

        # Verify job appears and ATS was auto-detected
        jobs = client.get("/api/jobs", headers=HEADERS).json()
        wh_job = [j for j in jobs if j["id"] == "test-webhook-001"]
        assert len(wh_job) == 1
        assert wh_job[0]["portal_type"] == "greenhouse"

    def test_sync_invalid_job(self, client):
        # Missing required fields — should log warning but not crash
        payload = {"jobs": [{"id": "bad-job"}]}
        res = client.post("/api/webhooks/jobs-sync", json=payload)
        assert res.status_code == 200
        assert res.json()["synced"] == 0


class TestStats:
    def test_stats(self, client):
        res = client.get("/api/stats", headers=HEADERS)
        assert res.status_code == 200
        data = res.json()
        assert "total" in data
        assert "by_status" in data
