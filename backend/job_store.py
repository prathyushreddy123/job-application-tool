from backend.models.job import Job, JobStatus


class JobStore:
    """In-memory store for jobs, keyed by UUID.

    Populated by n8n webhook sync or demo mode mock data.
    """

    def __init__(self):
        self._jobs: dict[str, Job] = {}

    def add_jobs(self, jobs: list[Job]):
        """Add or update jobs in the store."""
        for job in jobs:
            self._jobs[job.id] = job

    def get_job(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    def update_job(self, job_id: str, **kwargs) -> Job | None:
        job = self._jobs.get(job_id)
        if job is None:
            return None
        for key, value in kwargs.items():
            if hasattr(job, key):
                setattr(job, key, value)
        return job

    def get_all(self) -> list[Job]:
        return list(self._jobs.values())

    def get_by_status(self, status: JobStatus) -> list[Job]:
        return [j for j in self._jobs.values() if j.status == status]

    def count_by_status(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for job in self._jobs.values():
            key = job.status.value
            counts[key] = counts.get(key, 0) + 1
        return counts

    @property
    def size(self) -> int:
        return len(self._jobs)
