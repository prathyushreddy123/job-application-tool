from urllib.parse import urlparse

from backend.automation.adapters.base import BaseAdapter
from backend.automation.adapters.greenhouse import GreenhouseAdapter

# URL hostname patterns -> ATS type
_URL_PATTERNS: dict[str, str] = {
    "greenhouse.io": "greenhouse",
    "boards.greenhouse.io": "greenhouse",
    "grnh.se": "greenhouse",
    "myworkdayjobs.com": "workday",
    "wd5.myworkdayjobs.com": "workday",
    "myworkday.com": "workday",
    "lever.co": "lever",
    "jobs.lever.co": "lever",
    "linkedin.com": "linkedin",
}

# ATS type -> adapter class
_ADAPTERS: dict[str, type[BaseAdapter]] = {
    "greenhouse": GreenhouseAdapter,
}


def detect_ats_type(url: str) -> str:
    """Detect ATS type from a job URL pattern.

    Returns the ATS name (e.g., 'greenhouse', 'workday') or 'unknown'.
    """
    try:
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()
    except Exception:
        return "unknown"

    # Check from most specific to least specific
    for pattern, ats_type in _URL_PATTERNS.items():
        if pattern in hostname:
            return ats_type

    return "unknown"


def get_adapter(ats_type: str) -> BaseAdapter | None:
    """Get an adapter instance for the given ATS type.

    Returns None if no adapter is available for the type.
    """
    adapter_class = _ADAPTERS.get(ats_type)
    if adapter_class is None:
        return None
    return adapter_class()
