from __future__ import annotations

from fastapi import APIRouter

from recruitment_agent.api.v1 import candidates, interviews, jobs, matching, workflows

api_router = APIRouter()
api_router.include_router(candidates.router, prefix="/candidates", tags=["candidates"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(matching.router, prefix="/matching", tags=["matching"])
api_router.include_router(interviews.router, prefix="/interviews", tags=["interviews"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["workflows"])
