from backend.automation.ats_detect import detect_ats_type, get_adapter
from backend.automation.adapters.greenhouse import GreenhouseAdapter


class TestDetectAtsType:
    def test_greenhouse_boards_url(self):
        assert detect_ats_type("https://boards.greenhouse.io/techcorp/jobs/123") == "greenhouse"

    def test_greenhouse_embed_url(self):
        assert detect_ats_type("https://boards.greenhouse.io/embed/job_app?for=figma&token=123") == "greenhouse"

    def test_greenhouse_short_url(self):
        assert detect_ats_type("https://grnh.se/abc123") == "greenhouse"

    def test_workday_url(self):
        assert detect_ats_type("https://company.wd5.myworkdayjobs.com/en-US/careers/job/123") == "workday"

    def test_workday_generic_url(self):
        assert detect_ats_type("https://company.myworkdayjobs.com/jobs/123") == "workday"

    def test_lever_url(self):
        assert detect_ats_type("https://jobs.lever.co/company/abc-123") == "lever"

    def test_linkedin_url(self):
        assert detect_ats_type("https://www.linkedin.com/jobs/view/123456") == "linkedin"

    def test_unknown_url(self):
        assert detect_ats_type("https://careers.randomcompany.com/apply") == "unknown"

    def test_empty_url(self):
        assert detect_ats_type("") == "unknown"

    def test_malformed_url(self):
        assert detect_ats_type("not-a-url") == "unknown"


class TestGetAdapter:
    def test_greenhouse_adapter(self):
        adapter = get_adapter("greenhouse")
        assert adapter is not None
        assert isinstance(adapter, GreenhouseAdapter)
        assert adapter.name == "greenhouse"

    def test_unknown_adapter(self):
        assert get_adapter("unknown") is None

    def test_workday_not_implemented(self):
        assert get_adapter("workday") is None
