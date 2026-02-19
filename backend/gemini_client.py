import asyncio
import logging

from backend.models.job import Job

logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for Gemini AI to generate answers to custom job application questions.

    Uses the google-generativeai SDK (free tier). Falls back gracefully
    on failure — returns None so the field gets flagged as skipped.
    """

    def __init__(self, api_key: str):
        self._api_key = api_key
        self._model = None

        if api_key:
            try:
                import google.generativeai as genai

                genai.configure(api_key=api_key)
                self._model = genai.GenerativeModel("gemini-2.0-flash")
                logger.info("Gemini client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini: {e}")

    @property
    def is_available(self) -> bool:
        return self._model is not None

    async def generate_answer(
        self, question: str, profile: dict, job: Job
    ) -> str | None:
        """Generate a concise answer to a custom job application question.

        Args:
            question: The custom question text from the form.
            profile: The user's answers.json profile data.
            job: The job being applied to (for context).

        Returns:
            Generated answer string, or None on failure/timeout.
        """
        if not self.is_available:
            return None

        prompt = self._build_prompt(question, profile, job)

        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self._model.generate_content, prompt
                ),
                timeout=10.0,
            )
            answer = response.text.strip()

            # Sanity check: don't return empty or very long answers
            if not answer or len(answer) > 2000:
                return None

            logger.info(
                f"Gemini generated answer for '{question[:50]}...' "
                f"({len(answer)} chars)"
            )
            return answer

        except asyncio.TimeoutError:
            logger.warning(f"Gemini timeout for question: {question[:50]}...")
            return None
        except Exception as e:
            logger.warning(f"Gemini error: {e}")
            return None

    def _build_prompt(self, question: str, profile: dict, job: Job) -> str:
        personal = profile.get("personal", {})
        professional = profile.get("professional", {})
        name = personal.get("full_name", "the applicant")
        title = professional.get("current_title", "software engineer")
        experience = professional.get("years_experience", "several")

        return (
            f"You are helping {name}, a {title} with {experience} years of "
            f"experience, answer a job application question.\n\n"
            f"Company: {job.company}\n"
            f"Position: {job.job_title}\n"
            f"Question: {question}\n\n"
            f"Write a concise, professional answer (2-4 sentences max). "
            f"Be specific but not overly detailed. Use first person. "
            f"Do not include any greeting or sign-off. "
            f"Do not mention that you are an AI."
        )
