# app/agents/job_collector_agent.py

from app.collectors.remoteok import (
    collect_remoteok_jobs
)

from app.collectors.remotive import (
    collect_remotive_jobs
)

from app.collectors.wellfound import (
    collect_wellfound_jobs
)

from app.services.job_service import (
    save_job
)


class JobCollectorAgent:

    async def collect(self):

        jobs = []

        jobs.extend(
            await collect_remoteok_jobs()
        )

        jobs.extend(
            await collect_remotive_jobs()
        )

        jobs.extend(
            await collect_wellfound_jobs()
        )

        saved = 0

        for job in jobs:

            inserted = await save_job(job)

            if inserted:
                saved += 1

        return {
            "total_jobs": len(jobs),
            "saved_jobs": saved
        }