import json
from pathlib import Path

import pytest

from backend.profile import get_answer, load_profile, search_answer_bank


@pytest.fixture
def sample_profile(tmp_path: Path) -> dict:
    profile = {
        "personal": {
            "first_name": "Alex",
            "last_name": "Johnson",
            "email": "alex@email.com",
            "address": {"city": "San Francisco", "state": "CA"},
        },
        "professional": {"years_experience": "5"},
        "education": [
            {"degree": "BS", "school": "MIT"},
            {"degree": "MS", "school": "Stanford"},
        ],
        "custom_answers": {
            "willing_to_relocate": "Yes, I am open to relocation.",
            "work_authorization": "Authorized to work in the US.",
            "remote_work": "I thrive in remote environments.",
        },
    }
    (tmp_path / "answers.json").write_text(json.dumps(profile))
    return profile


def test_load_profile_valid(tmp_path: Path, sample_profile: dict):
    profile = load_profile(tmp_path)
    assert "personal" in profile
    assert "professional" in profile
    assert "custom_answers" in profile


def test_load_profile_missing_file(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="Profile not found"):
        load_profile(tmp_path / "nonexistent")


def test_get_answer_simple(sample_profile: dict):
    assert get_answer(sample_profile, "personal.first_name") == "Alex"


def test_get_answer_nested(sample_profile: dict):
    assert get_answer(sample_profile, "personal.address.city") == "San Francisco"


def test_get_answer_missing_key(sample_profile: dict):
    assert get_answer(sample_profile, "personal.middle_name") is None


def test_get_answer_returns_none_for_dict(sample_profile: dict):
    assert get_answer(sample_profile, "personal.address") is None


def test_get_answer_list_index(sample_profile: dict):
    assert get_answer(sample_profile, "education.0.degree") == "BS"
    assert get_answer(sample_profile, "education.1.school") == "Stanford"


def test_get_answer_list_index_out_of_bounds(sample_profile: dict):
    assert get_answer(sample_profile, "education.5.degree") is None


def test_get_answer_list_index_invalid(sample_profile: dict):
    assert get_answer(sample_profile, "education.abc.degree") is None


def test_search_answer_bank_match(sample_profile: dict):
    result = search_answer_bank(sample_profile, "Are you willing to relocate?")
    assert result == "Yes, I am open to relocation."


def test_search_answer_bank_remote(sample_profile: dict):
    result = search_answer_bank(sample_profile, "Do you have remote work experience?")
    assert result == "I thrive in remote environments."


def test_search_answer_bank_no_match(sample_profile: dict):
    result = search_answer_bank(sample_profile, "What is your favorite color?")
    assert result is None


def test_search_answer_bank_empty_bank():
    result = search_answer_bank({}, "Any question?")
    assert result is None
