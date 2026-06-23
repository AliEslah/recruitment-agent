from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import admin, auth, candidates, decisions, feedback, interviews, jobs, templates

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(jobs.router)
api_router.include_router(templates.router)
api_router.include_router(candidates.router)
api_router.include_router(interviews.router)
api_router.include_router(interviews.entry_router)
api_router.include_router(decisions.router)
api_router.include_router(feedback.router)
api_router.include_router(admin.router)
