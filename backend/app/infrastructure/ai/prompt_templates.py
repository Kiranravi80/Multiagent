"""
PAIOS Prompt Templates.

Centralized prompt management for all AI operations.
Separates prompt engineering from business logic.
"""

from __future__ import annotations

import json
from typing import Any


class PromptTemplates:
    """
    Collection of prompt templates for PAIOS AI operations.

    Each method returns a formatted prompt string.
    Templates are kept separate from business logic so they can be
    iterated on independently.
    """

    @staticmethod
    def resume_parser(resume_text: str) -> str:
        """Prompt for extracting structured data from a resume."""
        return f"""Extract information from the following resume.

Return ONLY valid JSON matching this exact schema:

{{
    "personal_details": {{
        "full_name": "",
        "email": "",
        "phone": "",
        "location": ""
    }},
    "social_profiles": {{
        "linkedin": "",
        "github": "",
        "portfolio": ""
    }},
    "education": [
        {{
            "institution": "",
            "degree": "",
            "field_of_study": "",
            "start_date": "",
            "end_date": "",
            "grade": "",
            "description": ""
        }}
    ],
    "skills": ["skill1", "skill2"],
    "projects": [
        {{
            "name": "",
            "description": "",
            "technologies": [],
            "url": "",
            "github_url": ""
        }}
    ],
    "experience": [
        {{
            "company": "",
            "title": "",
            "location": "",
            "start_date": "",
            "end_date": "",
            "is_current": false,
            "description": "",
            "technologies": []
        }}
    ],
    "certifications": [
        {{
            "name": "",
            "issuer": "",
            "date": "",
            "url": ""
        }}
    ],
    "achievements": ["achievement1"]
}}

Resume:

{resume_text}"""

    @staticmethod
    def profile_analyzer(profile_data: dict[str, Any]) -> str:
        """Prompt for analyzing a user profile and generating career insights."""
        return f"""Analyze this professional profile and provide career insights.

Return technical skills only. Do NOT return soft skills.
missing_skills should contain industry-relevant technical skills
needed for the recommended roles.

Return ONLY valid JSON matching this schema:

{{
    "experience_level": "junior|mid|senior|lead|principal",
    "total_experience_years": 0,
    "primary_domain": "",
    "secondary_domains": [],
    "recommended_roles": [],
    "core_skills": [],
    "missing_skills": [],
    "career_stage": ""
}}

Profile:

{json.dumps(profile_data, indent=2, default=str)}"""

    @staticmethod
    def job_classifier(job_data: dict[str, Any]) -> str:
        """Prompt for classifying a job as relevant or not."""
        return f"""Classify this job listing.

Determine if this is a relevant technical/software/AI/data job.
Non-technical jobs (sales, marketing, HR, etc.) are NOT relevant.

Return ONLY valid JSON:

{{
    "is_relevant": true,
    "category": "backend|frontend|fullstack|ai_ml|data|devops|mobile|other",
    "subcategory": "",
    "confidence": 0.95
}}

Job:

Title: {job_data.get('title', '')}
Company: {job_data.get('company', '')}
Description: {job_data.get('description', '')[:2000]}
Skills: {', '.join(job_data.get('skills', []))}"""

    @staticmethod
    def jd_analyzer(description: str) -> str:
        """Prompt for extracting structured data from a job description."""
        return f"""Extract structured requirements from this job description.

Return ONLY valid JSON:

{{
    "required_skills": ["skill1", "skill2"],
    "preferred_skills": ["skill1"],
    "experience_years": "3-5",
    "education": "Bachelor's in CS or equivalent",
    "keywords": ["keyword1", "keyword2"],
    "responsibilities": ["responsibility1"],
    "benefits": ["benefit1"],
    "work_type": "remote|onsite|hybrid"
}}

Job Description:

{description}"""

    @staticmethod
    def ats_evaluator(resume_text: str, jd_text: str) -> str:
        """Prompt for ATS compatibility evaluation."""
        return f"""Evaluate this resume against the job description for ATS compatibility.

Score each category from 0 to 100.
Provide specific, actionable improvements.

Return ONLY valid JSON:

{{
    "overall_score": 0,
    "keyword_score": 0,
    "formatting_score": 0,
    "sections_score": 0,
    "readability_score": 0,
    "improvements": [
        "specific improvement 1",
        "specific improvement 2"
    ],
    "missing_keywords": ["keyword1", "keyword2"],
    "strengths": ["strength1"]
}}

Resume:
{resume_text[:3000]}

Job Description:
{jd_text[:2000]}"""

    @staticmethod
    def recruiter_evaluator(resume_text: str, jd_text: str) -> str:
        """Prompt for recruiter perspective evaluation."""
        return f"""Act as a Senior Technical Recruiter reviewing this resume
against the job description.

Estimate probabilities as percentages (0-100).
Provide honest, specific feedback.

Return ONLY valid JSON:

{{
    "interview_probability": 0,
    "offer_probability": 0,
    "shortlist_probability": 0,
    "strengths": ["strength1"],
    "weaknesses": ["weakness1"],
    "improvements": ["improvement1"],
    "overall_assessment": ""
}}

Resume:
{resume_text[:3000]}

Job Description:
{jd_text[:2000]}"""

    @staticmethod
    def job_matcher(profile_data: dict[str, Any], jd_data: dict[str, Any]) -> str:
        """Prompt to score matching between user profile and job description analysis."""
        return f"""Evaluate the compatibility between this user profile and this job description.
        
        Score categories from 0 to 100.
        
        Return ONLY valid JSON matching this schema:
        {{
            "overall": 0.0,
            "skill": 0.0,
            "experience": 0.0,
            "education": 0.0,
            "location": 0.0,
            "salary": 0.0,
            "culture": 0.0,
            "notes": ""
        }}
        
        User Profile:
        {json.dumps(profile_data, indent=2, default=str)}
        
        Job Requirements:
        {json.dumps(jd_data, indent=2, default=str)}"""

    @staticmethod
    def resume_tailor(resume_text: str, jd_text: str) -> str:
        """Prompt to tailor a resume against a job description."""
        return f"""Tailor the following resume to align with the provided job description.
        
        Emphasize technical skills, experience details, and achievements matching the job description requirements.
        Do not falsify or fabricate any skills or experiences. Only re-phrase, organize, and emphasize relevant parts.
        
        Return ONLY the final tailored resume in clear, professional markdown or text format.
        
        Resume:
        {resume_text}
        
        Job Description:
        {jd_text}"""

