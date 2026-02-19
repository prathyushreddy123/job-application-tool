import pytest

from backend.gemini_client import GeminiClient
from backend.models.job import Job


def _make_job() -> Job:
    return Job(
        id="test-uuid",
        job_url="https://boards.greenhouse.io/test/jobs/1",
        company="TechCorp",
        job_title="Senior Engineer",
    )


def test_gemini_client_no_key():
    """Client without API key should not be available."""
    client = GeminiClient(api_key="")
    assert client.is_available is False


@pytest.mark.asyncio
async def test_gemini_generate_no_key():
    """Generate should return None when no API key is set."""
    client = GeminiClient(api_key="")
    result = await client.generate_answer(
        "Why do you want to work here?",
        {"personal": {"full_name": "Alex"}},
        _make_job(),
    )
    assert result is None


def test_gemini_build_prompt():
    """Prompt should include job and profile context."""
    client = GeminiClient(api_key="")
    profile = {
        "personal": {"full_name": "Alex Johnson"},
        "professional": {
            "current_title": "Software Engineer",
            "years_experience": "5",
        },
    }
    job = _make_job()
    prompt = client._build_prompt("Why this company?", profile, job)

    assert "Alex Johnson" in prompt
    assert "Software Engineer" in prompt
    assert "5" in prompt
    assert "TechCorp" in prompt
    assert "Senior Engineer" in prompt
    assert "Why this company?" in prompt
    assert "concise" in prompt.lower()
