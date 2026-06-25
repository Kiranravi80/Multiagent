"""
PAIOS Constants and Enumerations.

Centralized enums and constants used across all layers.
Prevents magic strings and ensures type safety.
"""

from __future__ import annotations

from enum import StrEnum, unique


# ── Agent Lifecycle ────────────────────────────────────────────────────────


@unique
class AgentStatus(StrEnum):
    """Runtime status of an AI agent."""

    IDLE = "idle"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    RECOVERING = "recovering"


# ── Job Domain ─────────────────────────────────────────────────────────────


@unique
class JobSource(StrEnum):
    """Supported job board sources."""

    LINKEDIN = "linkedin"
    NAUKRI = "naukri"
    FOUNDIT = "foundit"
    INDEED = "indeed"
    WELLFOUND = "wellfound"
    REMOTEOK = "remoteok"
    REMOTIVE = "remotive"
    YC_JOBS = "yc_jobs"
    COMPANY_CAREER = "company_career"


@unique
class JobStatus(StrEnum):
    """Processing pipeline status of a job listing."""

    NEW = "new"
    CLASSIFIED = "classified"
    ANALYZED = "analyzed"
    MATCHED = "matched"
    APPLIED = "applied"
    ARCHIVED = "archived"


@unique
class WorkType(StrEnum):
    """Job work arrangement type."""

    REMOTE = "remote"
    ONSITE = "onsite"
    HYBRID = "hybrid"
    UNKNOWN = "unknown"


# ── Match Confidence ───────────────────────────────────────────────────────


@unique
class MatchConfidence(StrEnum):
    """Confidence level for job match scores."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NO_MATCH = "no_match"


# ── Application Domain ────────────────────────────────────────────────────


@unique
class ApplicationStatus(StrEnum):
    """Status of a job application."""

    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    APPLIED = "applied"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    INTERVIEW_COMPLETED = "interview_completed"
    OFFER_RECEIVED = "offer_received"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


# ── Resume Domain ─────────────────────────────────────────────────────────


@unique
class ResumeType(StrEnum):
    """Type/variant of resume."""

    ORIGINAL = "original"
    AI_RESUME = "ai_resume"
    BACKEND = "backend"
    ML = "ml"
    FULLSTACK = "fullstack"
    FRONTEND = "frontend"
    DATA_ENGINEER = "data_engineer"
    DEVOPS = "devops"


# ── Event Types ────────────────────────────────────────────────────────────


@unique
class EventType(StrEnum):
    """All domain event types in the system (Message Bus)."""

    # System events
    SYSTEM_STARTED = "SYSTEM_STARTED"
    SYSTEM_SHUTDOWN = "SYSTEM_SHUTDOWN"
    AGENT_REGISTERED = "AGENT_REGISTERED"
    AGENT_STARTED = "AGENT_STARTED"
    AGENT_STOPPED = "AGENT_STOPPED"
    AGENT_ERROR = "AGENT_ERROR"
    HEALTH_CHECK = "HEALTH_CHECK"

    # User / Profile events
    USER_REGISTERED = "USER_REGISTERED"
    PROFILE_UPDATED = "PROFILE_UPDATED"
    PROFILE_ANALYZED = "PROFILE_ANALYZED"

    # Resume events
    RESUME_UPLOADED = "RESUME_UPLOADED"
    RESUME_PARSED = "RESUME_PARSED"
    RESUME_GENERATED = "RESUME_GENERATED"
    RESUME_TAILORED = "RESUME_TAILORED"

    # Career pipeline events
    JOB_COLLECTED = "JOB_COLLECTED"
    JOB_CLASSIFIED = "JOB_CLASSIFIED"
    JD_ANALYZED = "JD_ANALYZED"
    JOB_MATCHED = "JOB_MATCHED"
    ATS_COMPLETED = "ATS_COMPLETED"
    RECRUITER_EVALUATED = "RECRUITER_EVALUATED"

    # Application events
    APPLICATION_READY = "APPLICATION_READY"
    APPLICATION_APPROVED = "APPLICATION_APPROVED"
    APPLICATION_SUBMITTED = "APPLICATION_SUBMITTED"
    APPLICATION_UPDATED = "APPLICATION_UPDATED"

    # Intelligence events
    NEWS_COLLECTED = "NEWS_COLLECTED"
    DIGEST_GENERATED = "DIGEST_GENERATED"
    STARTUP_FOUND = "STARTUP_FOUND"
    FUNDING_DETECTED = "FUNDING_DETECTED"
    EVENT_FOUND = "EVENT_FOUND"
    EVENT_REMINDER = "EVENT_REMINDER"
    PAPER_FOUND = "PAPER_FOUND"
    TREND_DETECTED = "TREND_DETECTED"
    GITHUB_TREND_FOUND = "GITHUB_TREND_FOUND"

    # Engagement events
    CONTENT_GENERATED = "CONTENT_GENERATED"
    CONTENT_APPROVED = "CONTENT_APPROVED"
    MESSAGE_READY = "MESSAGE_READY"
    MESSAGE_APPROVED = "MESSAGE_APPROVED"
    OPPORTUNITY_FOUND = "OPPORTUNITY_FOUND"
    PORTFOLIO_UPDATED = "PORTFOLIO_UPDATED"

    # Learning events
    LEARNING_PLAN_CREATED = "LEARNING_PLAN_CREATED"
    SKILL_GAP_IDENTIFIED = "SKILL_GAP_IDENTIFIED"

    # Email / Calendar events
    EMAIL_READY = "EMAIL_READY"
    EMAIL_SENT = "EMAIL_SENT"
    CALENDAR_EVENT_CREATED = "CALENDAR_EVENT_CREATED"


# ── User Roles ─────────────────────────────────────────────────────────────


@unique
class UserRole(StrEnum):
    """Role-Based Access Control roles."""

    ADMIN = "admin"
    USER = "user"
    AGENT = "agent"  # System-level service account for agents


# ── Memory Types ───────────────────────────────────────────────────────────


@unique
class MemoryType(StrEnum):
    """Separate memory namespaces in the vector store."""

    CAREER = "career"
    LEARNING = "learning"
    NEWS = "news"
    RESEARCH = "research"
    NETWORKING = "networking"
    BUSINESS = "business"
    CONTENT = "content"
    LONG_TERM = "long_term"
    SEMANTIC = "semantic"
