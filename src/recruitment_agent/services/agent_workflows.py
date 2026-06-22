from __future__ import annotations

from recruitment_agent.agents.supervisor import RecruitmentSupervisor
from recruitment_agent.core.config import Settings


class AgentWorkflowService:
    def __init__(self, settings: Settings, supervisor: RecruitmentSupervisor | None = None) -> None:
        self.settings = settings
        self.supervisor = supervisor or RecruitmentSupervisor()

    def describe(self) -> dict[str, str]:
        return {
            "status": "ready",
            "orchestrator": "langgraph",
            "service": self.settings.app.name,
        }
