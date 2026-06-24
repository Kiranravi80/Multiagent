from fastapi import FastAPI
from app.routers.users import router as user_router
from app.routers.auth import router as auth_router
from app.routers.profile import router as profile_router
from app.routers.resume import router as resume_router
from app.routers.agent import router as agent_router
from app.dependencies.auth import get_current_user
from app.routers.jobs import router as jobs_router
from app.schedulers.scheduler import start_scheduler






app = FastAPI(
    title="Personal Job Agent API"
)

app.include_router(user_router)
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(resume_router)
app.include_router(agent_router)
app.include_router(jobs_router)


@app.get("/")
async def root():
    return {"message": "MongoDB Connected"}


@app.on_event("startup")
async def startup():
    start_scheduler()