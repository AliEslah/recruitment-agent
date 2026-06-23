from __future__ import annotations

GENERAL_SCORING_RULES = (
    "Return JSON only. Use only job-relevant evidence present in the input. "
    "Do not invent facts, employers, credentials, tools, links, or interview signals. "
    "Do not use protected attributes for scoring, questions, risks, or recommendations. "
    "Separate evidence, inference, missing evidence, and risk. Surface uncertainty and missing evidence explicitly. "
    "Provide calibrated confidence. Recommend a next human review step; never make the final hiring decision."
)
