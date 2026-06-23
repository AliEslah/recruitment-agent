from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import require_recruiter_user
from app.schemas.templates import RoleTemplateRead
from app.services.role_templates import get_role_template, load_role_templates

router = APIRouter(prefix="/templates", tags=["templates"], dependencies=[Depends(require_recruiter_user)])


@router.get("/roles", response_model=list[RoleTemplateRead])
async def list_role_templates() -> list[RoleTemplateRead]:
    return load_role_templates()


@router.get("/roles/{template_id}", response_model=RoleTemplateRead)
async def read_role_template(template_id: str) -> RoleTemplateRead:
    return get_role_template(template_id)
