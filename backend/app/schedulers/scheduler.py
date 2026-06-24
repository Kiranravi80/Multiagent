from apscheduler.schedulers.asyncio import (
    AsyncIOScheduler
)

from app.agents.job_collector_agent import (
    JobCollectorAgent
)

scheduler = AsyncIOScheduler()


async def collect_jobs():

    agent = JobCollectorAgent()

    await agent.collect()


def start_scheduler():

    scheduler.add_job(
        collect_jobs,
        "interval",
        minutes=15
    )

    scheduler.start()