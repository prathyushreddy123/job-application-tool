from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    NEW = "new"
    FILLING = "filling"
    READY = "ready"
    APPROVED = "approved"
    SUBMITTED = "submitted"
    FAILED = "failed"
    SKIPPED = "skipped"


class FilledField(BaseModel):
    label: str
    value: str = ""
    status: Literal["filled", "skipped", "ai_generated", "failed"] = "skipped"
    source: str = ""  # e.g. "personal.first_name", "gemini", "answer_bank"


class JobTiming(BaseModel):
    url_opened_at: str = ""
    form_filled_at: str = ""
    user_reviewed_at: str = ""
    submitted_at: str = ""


class Job(BaseModel):
    id: str
    job_url: str
    company: str
    job_title: str
    location: str = ""
    portal_type: str = ""
    priority: str = "medium"
    status: JobStatus = JobStatus.NEW
    date_added: str = ""
    fields: list[FilledField] = Field(default_factory=list)
    screenshot_path: str = ""
    error_log: str = ""
    timing: JobTiming = Field(default_factory=JobTiming)
