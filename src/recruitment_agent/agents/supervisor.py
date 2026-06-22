from __future__ import annotations

from typing import Any

from recruitment_agent.agents.graph import build_recruitment_graph
from recruitment_agent.agents.state import RecruitmentAgentState


class RecruitmentSupervisor:
    def __init__(self, graph: Any | None = None) -> None:
        self.graph = graph or build_recruitment_graph()

    async def run(self, initial_state: RecruitmentAgentState) -> RecruitmentAgentState:
        return await self.graph.ainvoke(initial_state)
