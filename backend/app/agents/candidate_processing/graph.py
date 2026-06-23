from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.agents.candidate_processing.nodes import (
    apply_basic_rules,
    build_enriched_profile,
    extract_links,
    extract_resume_text,
    load_candidate_and_job,
    parse_resume,
    persist_candidate_results,
    score_candidate,
)
from app.agents.candidate_processing.state import CandidateProcessingState


def build_candidate_processing_graph():
    builder = StateGraph(CandidateProcessingState)
    builder.add_node("load_candidate_and_job", load_candidate_and_job)
    builder.add_node("extract_resume_text", extract_resume_text)
    builder.add_node("parse_resume", parse_resume)
    builder.add_node("extract_links", extract_links)
    builder.add_node("build_enriched_profile", build_enriched_profile)
    builder.add_node("score_candidate", score_candidate)
    builder.add_node("apply_basic_rules", apply_basic_rules)
    builder.add_node("persist_candidate_results", persist_candidate_results)
    builder.add_edge(START, "load_candidate_and_job")
    builder.add_edge("load_candidate_and_job", "extract_resume_text")
    builder.add_edge("extract_resume_text", "parse_resume")
    builder.add_edge("parse_resume", "extract_links")
    builder.add_edge("extract_links", "build_enriched_profile")
    builder.add_edge("build_enriched_profile", "score_candidate")
    builder.add_edge("score_candidate", "apply_basic_rules")
    builder.add_edge("apply_basic_rules", "persist_candidate_results")
    builder.add_edge("persist_candidate_results", END)
    return builder.compile()


async def run_candidate_processing_graph(state: CandidateProcessingState) -> CandidateProcessingState:
    graph = build_candidate_processing_graph()
    return await graph.ainvoke(state)

