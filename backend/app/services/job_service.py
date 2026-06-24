# app/services/job_service.py

from datetime import datetime

from app.database import db


async def save_job(job: dict):

    fingerprint = (
        job["title"].lower().strip()
        +
        job["company"].lower().strip()
    )

    existing = await db.jobs.find_one(
        {
            "fingerprint": fingerprint
        }
    )

    if existing:
        return False

    job["fingerprint"] = fingerprint

    job["collected_at"] = datetime.utcnow()

    await db.jobs.insert_one(job)

    return True