from __future__ import annotations

from typing import NotRequired, TypedDict


class RecruitmentAgentState(TypedDict):
    workflow_id: NotRequired[str]
    request: NotRequired[str]
    job_id: NotRequired[str]
    candidate_ids: NotRequired[list[str]]
    messages: NotRequired[list[str]]
    result: NotRequired[str]
