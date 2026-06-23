from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin_user
from app.db.session import get_session
from app.repositories.logs import LogRepository
from app.schemas.common import AuditLogRead, CommunicationLogRead, LlmCallLogRead

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin_user)])


@router.get("/llm-usage", response_model=list[LlmCallLogRead])
async def llm_usage(limit: int = Query(default=100, le=500), session: AsyncSession = Depends(get_session)):
    return await LogRepository(session).llm_usage(limit)


@router.get("/audit", response_model=list[AuditLogRead])
async def audit(limit: int = Query(default=100, le=500), session: AsyncSession = Depends(get_session)):
    return await LogRepository(session).audit_logs(limit)


@router.get("/communications", response_model=list[CommunicationLogRead])
async def communications(limit: int = Query(default=100, le=500), session: AsyncSession = Depends(get_session)):
    return await LogRepository(session).communications(limit)
