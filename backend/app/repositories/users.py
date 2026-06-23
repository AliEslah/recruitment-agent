from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.db.models import User, UserRole


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, user_id: UUID) -> User:
        user = await self.session.get(User, user_id)
        if not user:
            raise NotFoundError("User not found.")
        return user

    async def get_by_email(self, email: str) -> User | None:
        normalized_email = email.strip().lower()
        return await self.session.scalar(select(User).where(User.email == normalized_email))

    async def upsert_dev_user(self, *, name: str, email: str, password_hash: str, role: UserRole) -> User:
        normalized_email = email.strip().lower()
        user = await self.get_by_email(normalized_email)
        if user:
            user.name = name
            user.password_hash = password_hash
            user.role = role
            user.is_active = True
        else:
            user = User(
                name=name,
                email=normalized_email,
                password_hash=password_hash,
                role=role,
                is_active=True,
            )
            self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
