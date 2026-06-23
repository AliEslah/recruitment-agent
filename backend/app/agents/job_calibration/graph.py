from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.agents.job_calibration.nodes import (
    extract_hiring_rubric,
    improve_jd,
    load_job,
    normalize_criteria_weights_node,
    persist_results,
    validate_rubric,
)
from app.agents.job_calibration.state import JobCalibrationState


def build_job_calibration_graph():
    builder = StateGraph(JobCalibrationState)
    builder.add_node("load_job", load_job)
    builder.add_node("improve_jd", improve_jd)
    builder.add_node("extract_hiring_rubric", extract_hiring_rubric)
    builder.add_node("normalize_criteria_weights", normalize_criteria_weights_node)
    builder.add_node("validate_rubric", validate_rubric)
    builder.add_node("persist_results", persist_results)
    builder.add_edge(START, "load_job")
    builder.add_edge("load_job", "improve_jd")
    builder.add_edge("improve_jd", "extract_hiring_rubric")
    builder.add_edge("extract_hiring_rubric", "normalize_criteria_weights")
    builder.add_edge("normalize_criteria_weights", "validate_rubric")
    builder.add_edge("validate_rubric", "persist_results")
    builder.add_edge("persist_results", END)
    return builder.compile()


async def run_job_calibration_graph(state: JobCalibrationState) -> JobCalibrationState:
    graph = build_job_calibration_graph()
    return await graph.ainvoke(state)

