"""Interview Router.

Provides endpoints to start mock prep sessions, retrieve question lists, and evaluate answers.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Body

from app.application.dependencies.auth import get_current_user
from app.application.dependencies.container import get_container
from app.domain.models.interview import InterviewModel

router = APIRouter(prefix="/interview", tags=["Interview Intelligence"])


@router.post("/sessions")
async def start_interview_session(
    job_id: str | None = None,
    role: str = "Senior Software Engineer",
    company: str = "Google",
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict:
    """Manually initiate a tailored mock interview prep session."""
    container = get_container()
    agent = container.orchestrator.registry.get("interview_agent")
    if not agent:
        raise HTTPException(status_code=500, detail="Interview agent not registered")

    context = {}
    if job_id:
        context["job_id"] = job_id
    else:
        # Create a mock job entry if job_id is empty to ensure generation works
        from app.domain.models.job import JobModel
        mock_job = JobModel(
            title=role,
            company=company,
            description="We are looking for an experienced developer with skills in Python, FastAPI, and MongoDB.",
            url="http://mockjob.com",
            source="company_career",
            fingerprint=f"mock_fingerprint_{role}_{company}".lower().replace(" ", "_")
        )
        try:
            job_id = await container.job_repo.create(mock_job)
        except Exception:
            # If unique index blocks, find the existing one
            jobs = await container.job_repo.find({"title": role, "company": company})
            if jobs:
                job_id = jobs[0].id
        context["job_id"] = job_id

    # Execute agent run
    result = await container.orchestrator.execute_agent("interview_agent", context=context)
    if not result.success:
        raise HTTPException(status_code=500, detail=result.message)

    interview_id = result.data.get("interview_id")
    return {
        "success": True,
        "interview_id": interview_id,
        "message": "Mock interview prep session initialized successfully."
    }


@router.get("/sessions/{id}")
async def get_interview_session(
    id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict:
    """Get details of a single mock interview prep session."""
    container = get_container()
    session = await container.interview_repo.get_by_id(id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview prep session not found")
    return session.model_dump()


@router.post("/sessions/{id}/answer")
async def answer_interview_question(
    id: str,
    question_index: int,
    user_answer: str = Body(...),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict:
    """Submit a response for a specific question, score it, and retrieve feedback."""
    container = get_container()
    session = await container.interview_repo.get_by_id(id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview prep session not found")

    if question_index < 0 or question_index >= len(session.questions):
        raise HTTPException(status_code=400, detail="Invalid question index")

    question_item = session.questions[question_index]

    # Evaluate answer via LLM
    llm_service = container.llm_service
    evaluation = await llm_service.evaluate_interview_answer(
        question=question_item["question"],
        ideal_answer=question_item["ideal_answer"],
        user_answer=user_answer
    )

    # Update question details in session
    question_item["user_answer"] = user_answer
    question_item["score"] = evaluation.get("score", 0.0)
    question_item["feedback"] = evaluation.get("feedback", "")
    question_item["strengths"] = evaluation.get("strengths", [])
    question_item["improvements"] = evaluation.get("improvements", [])

    # Re-calculate overall session status & average score
    answered_questions = [q for q in session.questions if q["user_answer"]]
    session.status = "in_progress"
    
    if len(answered_questions) == len(session.questions):
        session.status = "completed"
        total_score = sum(q["score"] for q in session.questions if q["score"] is not None)
        session.score = round(total_score / len(session.questions), 1)
        session.overall_feedback = f"Completed all questions with an average score of {session.score}%."

    session.updated_at = datetime.now(UTC)
    await container.interview_repo.update(session.id, session.to_dict())

    return {
        "success": True,
        "score": question_item["score"],
        "feedback": question_item["feedback"],
        "strengths": question_item["strengths"],
        "improvements": question_item["improvements"],
        "session_status": session.status,
        "session_overall_score": session.score
    }
