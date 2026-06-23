from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.agents.final_decision.nodes import (
    generate_final_scorecard,
    load_full_candidate_context,
    persist_final_scorecard,
    validate_final_scorecard,
)
from app.agents.final_decision.state import FinalDecisionState


def build_final_decision_graph():
    builder = StateGraph(FinalDecisionState)
    builder.add_node("load_full_candidate_context", load_full_candidate_context)
    builder.add_node("generate_final_scorecard", generate_final_scorecard)
    builder.add_node("validate_final_scorecard", validate_final_scorecard)
    builder.add_node("persist_final_scorecard", persist_final_scorecard)
    builder.add_edge(START, "load_full_candidate_context")
    builder.add_edge("load_full_candidate_context", "generate_final_scorecard")
    builder.add_edge("generate_final_scorecard", "validate_final_scorecard")
    builder.add_edge("validate_final_scorecard", "persist_final_scorecard")
    builder.add_edge("persist_final_scorecard", END)
    return builder.compile()


async def run_final_decision_graph(state: FinalDecisionState) -> FinalDecisionState:
    graph = build_final_decision_graph()
    return await graph.ainvoke(state)

