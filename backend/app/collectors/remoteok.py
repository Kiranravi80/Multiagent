import httpx
from bs4 import BeautifulSoup
from datetime import datetime

REMOTEOK_API = "https://remoteok.com/api"

ALLOWED_KEYWORDS = [
    "engineer",
    "developer",
    "software",
    "backend",
    "frontend",
    "full stack",
    "fullstack",
    "python",
    "java",
    "javascript",
    "typescript",
    "react",
    "node",
    "django",
    "fastapi",
    "flask",
    "ai",
    "machine learning",
    "data scientist",
    "data engineer",
    "devops",
    "cloud",
    "aws",
    "azure",
    "gcp",
    "docker",
    "kubernetes"
]

EXCLUDED_KEYWORDS = [
    "virtual assistant",
    "customer support",
    "data entry",
    "marketing",
    "sales",
    "finance",
    "accounting",
    "bookkeeping",
    "executive assistant",
    "hr",
    "human resources",
    "recruiter",
    "appointment setter",
    "cold calling",
    "call center",
    "insurance",
    "real estate",
    "office assistant",
    "administrative assistant"
]


def clean_html(html_text: str) -> str:
    return BeautifulSoup(
        html_text,
        "html.parser"
    ).get_text(
        separator=" ",
        strip=True
    )


def is_relevant_job(job: dict) -> bool:

    text = (
        f"{job['title']} "
        f"{job['description']} "
        f"{' '.join(job['skills'])}"
    ).lower()

    # Reject obvious non-tech jobs
    if any(
        keyword in text
        for keyword in EXCLUDED_KEYWORDS
    ):
        return False

    # Accept tech jobs
    if any(
        keyword in text
        for keyword in ALLOWED_KEYWORDS
    ):
        return True

    return False


async def collect_remoteok_jobs():

    jobs = []

    accepted = 0
    rejected = 0

    headers = {
        "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    try:

        async with httpx.AsyncClient(
            timeout=30
        ) as client:

            response = await client.get(
                REMOTEOK_API,
                headers=headers
            )

            response.raise_for_status()

            data = response.json()

            # First record is metadata
            data = data[1:]

            for item in data:

                try:

                    description = clean_html(
                        item.get(
                            "description",
                            ""
                        )
                    )

                    skills = [
                        tag.lower().strip()
                        for tag in item.get(
                            "tags",
                            []
                        )
                    ]

                    salary_min = item.get(
                        "salary_min",
                        0
                    )

                    salary_max = item.get(
                        "salary_max",
                        0
                    )

                    salary = ""

                    if salary_min and salary_max:

                        salary = (
                            f"${salary_min:,}"
                            f" - "
                            f"${salary_max:,}"
                        )

                    job = {

                        "job_id": str(
                            item.get(
                                "id",
                                ""
                            )
                        ),

                        "title": item.get(
                            "position",
                            ""
                        ).strip(),

                        "company": item.get(
                            "company",
                            ""
                        ).strip(),

                        "location": item.get(
                            "location",
                            "Remote"
                        ),

                        "salary": salary,

                        "description":
                        description,

                        "skills":
                        skills,

                        "experience_required":
                        "",

                        "work_type":
                        "Remote",

                        "source":
                        "remoteok",

                        "url":
                        item.get(
                            "url",
                            ""
                        ),

                        "posted_date":
                        item.get(
                            "date",
                            ""
                        ),

                        "collected_at":
                        datetime.utcnow()
                    }

                    # Validation
                    if not job["title"]:
                        continue

                    if not job["company"]:
                        continue

                    if len(
                        job["description"]
                    ) < 300:
                        continue

                    if not is_relevant_job(
                        job
                    ):
                        rejected += 1
                        continue

                    accepted += 1

                    jobs.append(job)

                except Exception as e:

                    print(
                        f"Job Parse Error: {e}"
                    )

                    continue

        print(
            f"\nRemoteOK Results"
        )

        print(
            f"Accepted Jobs: {accepted}"
        )

        print(
            f"Rejected Jobs: {rejected}"
        )

        print(
            f"Final Jobs: {len(jobs)}"
        )

        return jobs

    except Exception as e:

        print(
            f"RemoteOK Collector Failed: {e}"
        )

        return []