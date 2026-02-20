from fastapi import Header, HTTPException

from backend.config import get_settings


async def verify_api_key(x_api_key: str = Header(...)):
    """FastAPI dependency that validates the X-API-Key header."""
    settings = get_settings()
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
