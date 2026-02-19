import json
from pathlib import Path


def load_profile(data_dir: Path) -> dict:
    """Load user profile from answers.json."""
    path = data_dir / "answers.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Profile not found at {path}. "
            "Create data/answers.json with your form responses."
        )
    with open(path) as f:
        return json.load(f)


def get_answer(profile: dict, dotpath: str) -> str | None:
    """Traverse nested dict by dot-separated path.

    Example: get_answer(profile, "personal.address.city") -> "San Francisco"
    Returns None if any key in the path is missing.
    """
    current = profile
    for key in dotpath.split("."):
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    if isinstance(current, (dict, list)):
        return None
    return str(current)


def search_answer_bank(profile: dict, question: str) -> str | None:
    """Search custom_answers for a keyword match against the question.

    Uses simple keyword overlap: each key in custom_answers is split into
    words, and if any word (3+ chars) appears in the question, it's a match.
    Returns the best match (most keyword overlap) or None.
    """
    bank = profile.get("custom_answers", {})
    if not bank:
        return None

    question_lower = question.lower()
    best_match = None
    best_score = 0

    for key, answer in bank.items():
        keywords = key.lower().replace("_", " ").split()
        score = sum(
            1 for word in keywords
            if len(word) >= 3 and word in question_lower
        )
        if score > best_score:
            best_score = score
            best_match = answer

    return best_match if best_score > 0 else None
