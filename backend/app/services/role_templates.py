from __future__ import annotations

import json
from functools import lru_cache
from importlib.resources import files
from typing import Any

from app.core.errors import NotFoundError
from app.schemas.templates import RoleTemplateRead


def _load_json_fixture(name: str) -> list[dict[str, Any]]:
    fixture = files("app.fixtures").joinpath(name)
    return json.loads(fixture.read_text(encoding="utf-8"))


@lru_cache
def load_role_templates() -> list[RoleTemplateRead]:
    return [RoleTemplateRead.model_validate(item) for item in _load_json_fixture("role_templates.json")]


def get_role_template(template_id: str) -> RoleTemplateRead:
    for template in load_role_templates():
        if template.template_id == template_id:
            return template
    raise NotFoundError("Role template not found.")
