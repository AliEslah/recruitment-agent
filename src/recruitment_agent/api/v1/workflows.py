from __future__ import annotations

from fastapi import APIRouter, Depends

from recruitment_agent.api.deps import agent_workflow_service_dependency
from recruitment_agent.services.agent_workflows import AgentWorkflowService

router = APIRouter()


@router.get("")
async def list_workflows(
    service: AgentWorkflowService = Depends(agent_workflow_service_dependency),
) -> dict[str, str]:
    return service.describe()
