# app/collectors/base.py

from pydantic import BaseModel


class Job(BaseModel):

    title: str
    company: str
    location: str

    description: str

    salary: str | None = None

    experience_required: str | None = None

    source: str

    url: str

    posted_date: str | None = None