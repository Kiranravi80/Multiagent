"""
Resume Application Service.

Handles resume upload, parsing, and link extraction.
"""

from __future__ import annotations

import re
from typing import Any

import pdfplumber

from app.core.exceptions import DomainValidationError, EntityNotFoundError
from app.core.logging import get_logger
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.ai.llm_service import LLMService
from app.infrastructure.storage.file_storage import FileStorage

logger = get_logger(__name__)


class ResumeService:
    """Resume upload, parse, and extraction operations."""

    def __init__(
        self,
        *,
        user_repo: UserRepository,
        llm_service: LLMService,
        file_storage: FileStorage,
    ) -> None:
        self._user_repo = user_repo
        self._llm = llm_service
        self._storage = file_storage

    async def upload_resume(
        self,
        *,
        user_id: str,
        email: str,
        filename: str,
        content: bytes,
    ) -> dict[str, Any]:
        """
        Upload a resume PDF, extract text and links, store metadata.
        """
        # Save file
        safe_filename = f"{user_id}_{filename}"
        file_path = await self._storage.save_upload(
            content, subdirectory="resumes", filename=safe_filename
        )

        # Extract text
        resume_text = self._extract_text_from_pdf(str(file_path))
        if not resume_text.strip():
            raise DomainValidationError("Could not extract text from PDF", field="file")

        # Extract links
        links = self._extract_links(resume_text)

        # Update user record
        update_data: dict[str, Any] = {
            "resume_file_path": str(file_path),
            "resume_text": resume_text,
        }
        if links["linkedin"]:
            update_data["social_profiles.linkedin"] = links["linkedin"]
        if links["github"]:
            update_data["social_profiles.github"] = links["github"]
        if links["portfolio"]:
            update_data["social_profiles.portfolio"] = links["portfolio"]

        await self._user_repo.update_profile(email, update_data)

        logger.info("resume_uploaded", user_id=user_id, filename=filename)

        return {
            "message": "Resume uploaded successfully",
            "linkedin": links["linkedin"],
            "github": links["github"],
            "portfolio": links["portfolio"],
        }

    async def parse_resume(self, *, email: str) -> dict[str, Any]:
        """
        Parse an uploaded resume using AI and update the user profile.
        """
        user = await self._user_repo.find_by_email(email)
        if user is None:
            raise EntityNotFoundError("User", email)

        resume_text = user.resume_text
        if not resume_text:
            raise DomainValidationError("No resume uploaded yet", field="resume")

        # AI parsing
        parsed_data = await self._llm.parse_resume(resume_text)

        # Update user profile with parsed data
        update_fields = {}
        for key in [
            "personal_details", "social_profiles", "education",
            "skills", "projects", "experience",
            "certifications", "achievements",
        ]:
            if key in parsed_data:
                update_fields[key] = parsed_data[key]

        if update_fields:
            await self._user_repo.update_profile(email, update_fields)

        logger.info("resume_parsed", email=email, sections=list(parsed_data.keys()))

        return {"message": "Resume parsed successfully", "data": parsed_data}

    # ── Private helpers ────────────────────────────────────────────────────

    @staticmethod
    def _extract_text_from_pdf(file_path: str) -> str:
        """Extract text from a PDF file."""
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text

    @staticmethod
    def _extract_links(text: str) -> dict[str, str]:
        """Extract LinkedIn, GitHub, and portfolio links from text."""
        linkedin = ""
        github = ""
        portfolio = ""

        linkedin_match = re.search(
            r"(?:https?://)?(?:www\.)?linkedin\.com/in/[^\s]+",
            text, re.IGNORECASE,
        )
        github_match = re.search(
            r"(?:https?://)?(?:www\.)?github\.com/[^\s]+",
            text, re.IGNORECASE,
        )
        portfolio_match = re.search(
            r"[a-zA-Z0-9\-]+\.vercel\.app",
            text, re.IGNORECASE,
        )

        if linkedin_match:
            linkedin = linkedin_match.group()
        if github_match:
            github = github_match.group()
        if portfolio_match:
            portfolio = portfolio_match.group()

        return {"linkedin": linkedin, "github": github, "portfolio": portfolio}
