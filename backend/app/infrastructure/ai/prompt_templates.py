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

    @staticmethod
    def learning_plan_generator(skills_user: list[str], target_skills: list[str]) -> str:
        """Prompt to generate a structured learning plan for missing skills."""
        return f"""Act as an expert technical mentor. Generate a structured, step-by-step learning plan to help a software engineer bridge the gap between their current skills and target skills.
        
        Current Skills: {', '.join(skills_user)}
        Target/Missing Skills to acquire: {', '.join(target_skills)}
        
        Provide actionable study blocks, estimated hours, and descriptions for each topic.
        
        Return ONLY valid JSON matching this schema:
        {{
            "title": "Learning Plan Name",
            "tasks": [
                {{
                    "topic": "Topic Name",
                    "description": "What to study and practice",
                    "estimated_hours": 4.5
                }}
            ]
        }}"""

    @staticmethod
    def content_generator(platform: str, topic: str, user_bio: str) -> str:
        """Prompt to generate professional posts/content drafts."""
        return f"""Act as a seasoned tech industry leader and influencer.
        Draft a high-impact, professional content post for {platform} on the topic: "{topic}".
        Use a natural, technical, and engaging tone. Avoid generic buzzwords.
        
        User Professional Context:
        {user_bio}
        
        Return a JSON object with "title" and "body" keys.
        Return ONLY valid JSON:
        {{
            "title": "A compelling title or hook",
            "body": "The complete post content, formatted with line breaks if appropriate"
        }}"""

    @staticmethod
    def portfolio_updater(profile_data: dict[str, Any], projects: list[dict[str, Any]]) -> str:
        """Prompt to generate or update portfolio layout and featured details."""
        return f"""Generate a structured portfolio page layout configuration based on the user's profile and projects.
        
        Profile Data:
        {json.dumps(profile_data, indent=2, default=str)}
        
        Projects:
        {json.dumps(projects, indent=2, default=str)}
        
        Return ONLY valid JSON matching this schema:
        {{
            "bio": "A catchy, brief professional bio for a personal website",
            "skills": ["skill1", "skill2"],
            "projects": [
                {{
                    "title": "Project Name",
                    "description": "Brief 1-2 sentence description",
                    "technologies": ["tech1"],
                    "github_url": "",
                    "live_url": ""
                }}
            ],
            "socials": {{
                "linkedin": "",
                "github": "",
                "email": ""
            }},
            "layout": {{
                "theme": "dark-glassmorphism",
                "columns": 2,
                "sections_order": ["header", "bio", "skills", "projects", "contact"]
            }}
        }}"""

    @staticmethod
    def outreach_drafter(profile_data: dict[str, Any], target_contact: dict[str, Any]) -> str:
        """Prompt to draft targeted recruiter/lead outreach messages."""
        return f"""Draft a professional, short, and highly personalized outreach message to a contact.
        Make it sound authentic, respectful, and short (under 300 characters for LinkedIn, or a short email).
        
        User Profile:
        {json.dumps(profile_data, indent=2, default=str)}
        
        Target Contact:
        {json.dumps(target_contact, indent=2, default=str)}
        
        Return ONLY valid JSON matching this schema:
        {{
            "subject": "Outreach Subject Line (if email, otherwise empty)",
            "message": "The personalized connection note or message"
        }}"""

    @staticmethod
    def email_responder(inbound_email: str, user_profile: dict[str, Any]) -> str:
        """Prompt to draft email response options."""
        return f"""Act as the user's AI chief-of-staff. Read this inbound recruiter/hiring email and draft a professional reply.
        Ensure it aligns with the user's profile, highlights interest, and seeks to schedule a conversation.
        
        Inbound Email:
        {inbound_email}
        
        User Profile:
        {json.dumps(user_profile, indent=2, default=str)}
        
        Return ONLY valid JSON matching this schema:
        {{
            "subject": "Re: original subject or appropriate reply subject",
            "body": "The drafted email response"
        }}"""

    @staticmethod
    def interview_generator(role: str, company: str, resume_text: str, jd_text: str | None = None) -> str:
        """Prompt to generate mock interview questions."""
        return f"""Generate 5 targeted, highly technical mock interview questions for a candidate.
        Target Role: {role}
        Target Company: {company}
        
        Candidate Resume:
        {resume_text[:2000]}
        
        Job Description:
        {(jd_text or "")[:2000]}
        
        Provide a mixture of resume-specific, coding, system design, and behavioral questions.
        For each question, provide a detailed "ideal_answer" summary.
        
        Return ONLY valid JSON matching this schema:
        {{
            "questions": [
                {{
                    "question": "Question text here",
                    "type": "technical|behavioral|resume",
                    "ideal_answer": "Key points that should be in the candidate's answer"
                }}
            ]
        }}"""

    @staticmethod
    def interview_evaluator(question: str, ideal_answer: str, user_answer: str) -> str:
        """Prompt to evaluate mock interview answer."""
        return f"""Act as a principal software interviewer. Evaluate the candidate's answer to this mock interview question.
        Compare it against the ideal answer expectations.
        
        Question:
        {question}
        
        Ideal Answer Expectation:
        {ideal_answer}
        
        Candidate's Answer:
        {user_answer}
        
        Grade the answer from 0.0 to 100.0. Provide specific missing points and constructive feedback.
        
        Return ONLY valid JSON matching this schema:
        {{
            "score": 85.0,
            "feedback": "A general summary of their performance",
            "strengths": ["what they did well"],
            "improvements": ["what was missing or wrong"]
        }}"""



