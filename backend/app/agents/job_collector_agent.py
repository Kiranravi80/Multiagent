"""Job Collector Agent.

Periodically collects tech jobs from remote boards, validates them, and saves to database.
"""

from __future__ import annotations

from typing import Any

from app.agents.base.agent import BaseAgent, AgentResult
from app.core.constants import JobSource, WorkType, EventType
from app.domain.models.job import JobModel, SalaryRange
from app.domain.repositories.job_repository import JobRepository
from app.domain.events.base import DomainEvent
from app.collectors.remoteok import collect_remoteok_jobs
from app.collectors.remotive import collect_remotive_jobs
from app.collectors.wellfound import collect_wellfound_jobs


class JobCollectorAgent(BaseAgent):
    """AI agent that pulls and consolidates job listings from multiple sources."""

    def __init__(self, *, event_bus: Any, job_repo: JobRepository) -> None:
        super().__init__(name="job_collector_agent", event_bus=event_bus)
        self._job_repo = job_repo

    async def initialize(self) -> None:
        """Initialize resources and configurations."""
        self._logger.info("job_collector_agent_initialized")

    async def execute(self, context: dict[str, Any] | None = None) -> AgentResult:
        """Execute the collection routine."""
        self._logger.info("job_collection_started")

        raw_jobs = []

        # 1. Scrape RemoteOK
        try:
            remoteok_jobs = await collect_remoteok_jobs()
            raw_jobs.extend(remoteok_jobs)
        except Exception as exc:
            self._logger.error("remoteok_collection_failed", error=str(exc))

        # 2. Scrape Remotive
        try:
            remotive_jobs = await collect_remotive_jobs()
            raw_jobs.extend(remotive_jobs)
        except Exception as exc:
            self._logger.error("remotive_collection_failed", error=str(exc))

        # 3. Scrape Wellfound
        try:
            wellfound_jobs = await collect_wellfound_jobs()
            raw_jobs.extend(wellfound_jobs)
        except Exception as exc:
            self._logger.error("wellfound_collection_failed", error=str(exc))

        saved_count = 0
        job_models = []

        for job_data in raw_jobs:
            try:
                # Map work type
                wt_str = job_data.get("work_type", "").lower()
                work_type = WorkType.REMOTE if "remote" in wt_str else WorkType.UNKNOWN

                # Map source
                src_str = job_data.get("source", "").lower()
                source = JobSource.REMOTEOK
                if src_str == "remotive":
                    source = JobSource.REMOTIVE
                elif src_str == "wellfound":
                    source = JobSource.WELLFOUND

                # Parse salary range
                sal_range = SalaryRange()
                salary_str = job_data.get("salary", "")
                if salary_str and "$" in salary_str:
                    parts = [p.strip().replace("$", "").replace(",", "") for p in salary_str.split("-")]
                    try:
                        if len(parts) >= 1 and parts[0].isdigit():
                            sal_range.min_value = int(parts[0])
                        if len(parts) >= 2 and parts[1].isdigit():
                            sal_range.max_value = int(parts[1])
                    except Exception:
                        pass

                # Build model
                job = JobModel(
                    job_id=job_data.get("job_id", ""),
                    title=job_data.get("title", ""),
                    company=job_data.get("company", ""),
                    location=job_data.get("location", "Remote"),
                    description=job_data.get("description", ""),
                    skills=job_data.get("skills", []),
                    salary=sal_range,
                    experience_required=job_data.get("experience_required", ""),
                    work_type=work_type,
                    source=source,
                    url=job_data.get("url", ""),
                    posted_date=job_data.get("posted_date", ""),
                )

                if not job.is_valid_for_collection():
                    continue

                job_models.append(job)
            except Exception as exc:
                self._logger.debug("job_mapping_skipped", error=str(exc))

        if job_models:
            try:
                saved_count = await self._job_repo.bulk_create(job_models)
            except Exception as exc:
                self._logger.error("jobs_bulk_create_failed", error=str(exc))
                # Fallback to single inserts
                for job in job_models:
                    try:
                        inserted_id = await self._job_repo.create(job)
                        if inserted_id:
                            saved_count += 1
                    except Exception:
                        pass

        self._logger.info("job_collection_completed", total_scraped=len(raw_jobs), saved=saved_count)

        # Publish status event
        event = DomainEvent(
            event_type=EventType.JOB_COLLECTED,
            source_agent=self.name,
            payload={
                "scraped_count": len(raw_jobs),
                "saved_count": saved_count,
            }
        )
        await self.publish_event(event)

        return AgentResult(
            success=True,
            data={
                "scraped_count": len(raw_jobs),
                "saved_count": saved_count,
            },
            message=f"Successfully collected {len(raw_jobs)} jobs, saved {saved_count} new entries."
        )