from fastapi import APIRouter, Depends

from backend.auth import verify_api_key
from backend.stats import get_stats

router = APIRouter(prefix="/api", dependencies=[Depends(verify_api_key)])


@router.get("/stats")
async def stats():
    """Get aggregated stats from audit logs."""
    from backend.main import app_state

    return get_stats(app_state.settings.data_dir)
