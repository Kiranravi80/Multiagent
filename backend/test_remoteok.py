import asyncio

from app.collectors.remoteok import (
    collect_remoteok_jobs
)


async def main():

    jobs = await collect_remoteok_jobs()

    print(
        f"\nTotal Jobs: {len(jobs)}"
    )

    for job in jobs[:5]:

        print("\n----------------")
        print(job["title"])
        print(job["company"])
        print(job["skills"][:5])


asyncio.run(main())