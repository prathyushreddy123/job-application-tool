import pytest

from backend.config import Settings
from backend.n8n_client import N8nClient


def test_n8n_client_init():
    """Client should initialize with correct webhook URL."""
    settings = Settings(
        n8n_url="http://localhost:5678",
        n8n_webhook_url="http://localhost:5678/webhook",
    )
    client = N8nClient(settings)
    assert client._webhook_url == "http://localhost:5678/webhook"
    assert client.queued_count == 0
    assert client.is_online is False  # Not started yet


@pytest.mark.asyncio
async def test_n8n_client_queues_on_failure():
    """Calls to unreachable n8n should be queued for retry."""
    settings = Settings(
        n8n_url="http://localhost:19999",  # Not running
        n8n_webhook_url="http://localhost:19999/webhook",
    )
    client = N8nClient(settings)

    # Call without starting (no retry loop) — should queue
    await client._post("test-endpoint", {"key": "value"})
    assert client.queued_count == 1

    await client._post("test-endpoint-2", {"key": "value2"})
    assert client.queued_count == 2

    await client._client.aclose()


@pytest.mark.asyncio
async def test_n8n_health_check_offline():
    """Health check should return False when n8n is unreachable."""
    settings = Settings(
        n8n_url="http://localhost:19999",
        n8n_webhook_url="http://localhost:19999/webhook",
    )
    client = N8nClient(settings)
    result = await client._check_health()
    assert result is False
    await client._client.aclose()


@pytest.mark.asyncio
async def test_n8n_health_check_online():
    """Health check should return True when n8n is running."""
    settings = Settings(
        n8n_url="http://localhost:5678",
        n8n_webhook_url="http://localhost:5678/webhook",
    )
    client = N8nClient(settings)
    result = await client._check_health()
    # This test passes only when n8n is actually running
    assert result is True
    await client._client.aclose()
