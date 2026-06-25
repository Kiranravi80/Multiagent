"""
Unified LLM Service.

High-level service that combines ModelManager with PromptTemplates
for common AI operations used across agents.
"""

from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.infrastructure.ai.model_manager import ModelManager
from app.infrastructure.ai.prompt_templates import PromptTemplates

logger = get_logger(__name__)


class LLMService:
    """
    Provides ready-to-use AI operations for agents.

    Combines ModelManager (inference) with PromptTemplates (prompts)
    into a single clean interface.
    """

    def __init__(self, model_manager: ModelManager) -> None:
        self._model = model_manager
        self._prompts = PromptTemplates()

    async def parse_resume(self, resume_text: str) -> dict[str, Any]:
        """Parse a resume into structured data."""
        prompt = self._prompts.resume_parser(resume_text)
        result = await self._model.generate_json(prompt)
        logger.info("resume_parsed_by_ai", sections=list(result.keys()))
        return result

    async def analyze_profile(self, profile_data: dict[str, Any]) -> dict[str, Any]:
        """Analyze a user profile for career insights."""
        prompt = self._prompts.profile_analyzer(profile_data)
        result = await self._model.generate_json(prompt)
        logger.info("profile_analyzed_by_ai", primary_domain=result.get("primary_domain"))
        return result

    async def classify_job(self, job_data: dict[str, Any]) -> dict[str, Any]:
        """Classify a job as relevant/irrelevant."""
        prompt = self._prompts.job_classifier(job_data)
        return await self._model.generate_json(prompt)

    async def analyze_jd(self, description: str) -> dict[str, Any]:
        """Extract structured requirements from a job description."""
        prompt = self._prompts.jd_analyzer(description)
        return await self._model.generate_json(prompt)

    async def evaluate_ats(self, resume_text: str, jd_text: str) -> dict[str, Any]:
        """Evaluate ATS compatibility of a resume against a JD."""
        prompt = self._prompts.ats_evaluator(resume_text, jd_text)
        return await self._model.generate_json(prompt)

    async def evaluate_recruiter(self, resume_text: str, jd_text: str) -> dict[str, Any]:
        """Get recruiter perspective on resume vs JD."""
        prompt = self._prompts.recruiter_evaluator(resume_text, jd_text)
        return await self._model.generate_json(prompt)

    async def match_job(self, profile_data: dict[str, Any], jd_data: dict[str, Any]) -> dict[str, Any]:
        """Score matching between user profile and job requirements."""
        prompt = self._prompts.job_matcher(profile_data, jd_data)
        return await self._model.generate_json(prompt)

    async def tailor_resume(self, resume_text: str, jd_text: str) -> str:
        """Tailor a resume to fit a job description."""
        prompt = self._prompts.resume_tailor(resume_text, jd_text)
        return await self._model.generate(prompt)

    async def generate_learning_plan(self, skills_user: list[str], target_skills: list[str]) -> dict[str, Any]:
        """Generate a structured learning plan based on skill gaps."""
        prompt = self._prompts.learning_plan_generator(skills_user, target_skills)
        return await self._model.generate_json(prompt)

    async def generate_content(self, platform: str, topic: str, user_bio: str) -> dict[str, Any]:
        """Generate technical content drafts."""
        prompt = self._prompts.content_generator(platform, topic, user_bio)
        return await self._model.generate_json(prompt)

    async def generate_portfolio_config(self, profile_data: dict[str, Any], projects: list[dict[str, Any]]) -> dict[str, Any]:
        """Generate/update personal portfolio configurations."""
        prompt = self._prompts.portfolio_updater(profile_data, projects)
        return await self._model.generate_json(prompt)

    async def draft_outreach(self, profile_data: dict[str, Any], target_contact: dict[str, Any]) -> dict[str, Any]:
        """Draft personalized recruiter/hiring lead outreach notes."""
        prompt = self._prompts.outreach_drafter(profile_data, target_contact)
        return await self._model.generate_json(prompt)

    async def draft_email_reply(self, inbound_email: str, user_profile: dict[str, Any]) -> dict[str, Any]:
        """Draft a reply to recruiter emails."""
        prompt = self._prompts.email_responder(inbound_email, user_profile)
        return await self._model.generate_json(prompt)

    async def generate_interview_questions(self, role: str, company: str, resume_text: str, jd_text: str | None = None) -> dict[str, Any]:
        """Generate mock interview technical and behavioral questions."""
        prompt = self._prompts.interview_generator(role, company, resume_text, jd_text)
        return await self._model.generate_json(prompt)

    async def evaluate_interview_answer(self, question: str, ideal_answer: str, user_answer: str) -> dict[str, Any]:
        """Evaluate a mock interview response and score it."""
        prompt = self._prompts.interview_evaluator(question, ideal_answer, user_answer)
        return await self._model.generate_json(prompt)

    async def generate_text(
        self,
        prompt: str,
        *,
        system: str = "",
        temperature: float = 0.7,
    ) -> str:
        """General-purpose text generation."""
        return await self._model.generate(prompt, system=system, temperature=temperature)
