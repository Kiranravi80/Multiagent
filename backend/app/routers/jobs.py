# app/routers/jobs.py

from fastapi import APIRouter

from app.agents.job_collector_agent import (
    JobCollectorAgent
)

router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"]
)


@router.post("/collect")
async def collect_jobs():

    agent = JobCollectorAgent()

    return await agent.collect()