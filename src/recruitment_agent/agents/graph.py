from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from recruitment_agent.agents.state import RecruitmentAgentState


def initialize_workflow(state: RecruitmentAgentState) -> dict[str, str]:
    return {"result": state.get("result", "workflow scaffold initialized")}


def build_recruitment_graph():
    builder = StateGraph(RecruitmentAgentState)
    builder.add_node("initialize_workflow", initialize_workflow)
    builder.add_edge(START, "initialize_workflow")
    builder.add_edge("initialize_workflow", END)
    return builder.compile()
