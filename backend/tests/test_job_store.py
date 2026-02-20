from backend.job_store import JobStore
from backend.models.job import Job, JobStatus


def _make_job(id: str = "uuid-1", status: JobStatus = JobStatus.NEW) -> Job:
    return Job(
        id=id,
        job_url=f"https://boards.greenhouse.io/test/jobs/{id}",
        company="TestCorp",
        job_title="Engineer",
        status=status,
    )


class TestJobStore:
    def test_add_and_get(self):
        store = JobStore()
        job = _make_job()
        store.add_jobs([job])
        assert store.get_job("uuid-1") is not None
        assert store.get_job("uuid-1").company == "TestCorp"

    def test_get_nonexistent(self):
        store = JobStore()
        assert store.get_job("nonexistent") is None

    def test_get_all(self):
        store = JobStore()
        store.add_jobs([_make_job("a"), _make_job("b"), _make_job("c")])
        assert len(store.get_all()) == 3

    def test_update_job(self):
        store = JobStore()
        store.add_jobs([_make_job()])
        updated = store.update_job("uuid-1", status=JobStatus.SUBMITTED)
        assert updated is not None
        assert updated.status == JobStatus.SUBMITTED

    def test_update_nonexistent(self):
        store = JobStore()
        assert store.update_job("nonexistent", status=JobStatus.FAILED) is None

    def test_get_by_status(self):
        store = JobStore()
        store.add_jobs([
            _make_job("a", JobStatus.NEW),
            _make_job("b", JobStatus.SUBMITTED),
            _make_job("c", JobStatus.NEW),
        ])
        new_jobs = store.get_by_status(JobStatus.NEW)
        assert len(new_jobs) == 2

    def test_count_by_status(self):
        store = JobStore()
        store.add_jobs([
            _make_job("a", JobStatus.NEW),
            _make_job("b", JobStatus.SUBMITTED),
            _make_job("c", JobStatus.NEW),
            _make_job("d", JobStatus.FAILED),
        ])
        counts = store.count_by_status()
        assert counts["new"] == 2
        assert counts["submitted"] == 1
        assert counts["failed"] == 1

    def test_size(self):
        store = JobStore()
        assert store.size == 0
        store.add_jobs([_make_job("a"), _make_job("b")])
        assert store.size == 2

    def test_add_overwrites_existing(self):
        store = JobStore()
        store.add_jobs([_make_job("a")])
        updated = _make_job("a")
        updated.company = "NewCorp"
        store.add_jobs([updated])
        assert store.size == 1
        assert store.get_job("a").company == "NewCorp"
