from __future__ import annotations

from recruitment_agent.agents.graph import build_recruitment_graph


def test_recruitment_graph_compiles_and_runs() -> None:
    graph = build_recruitment_graph()

    result = graph.invoke({"request": "screen candidates"})

    assert result["result"] == "workflow scaffold initialized"
