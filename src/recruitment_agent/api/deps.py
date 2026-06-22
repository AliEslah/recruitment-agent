from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from recruitment_agent.core.config import Settings, get_settings
from recruitment_agent.db.session import get_async_session
from recruitment_agent.services.agent_workflows import AgentWorkflowService


def settings_dependency() -> Settings:
    return get_settings()


async def db_session_dependency() -> AsyncIterator[AsyncSession]:
    async for session in get_async_session():
        yield session


def agent_workflow_service_dependency(
    settings: Settings = Depends(settings_dependency),
) -> AgentWorkflowService:
    return AgentWorkflowService(settings=settings)
