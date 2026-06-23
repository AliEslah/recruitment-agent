from __future__ import annotations

import asyncio

from app.core.config import get_settings
from app.db.models import UserRole
from app.db.session import AsyncSessionLocal
from app.repositories.users import UserRepository
from app.services.auth import hash_password


async def main() -> None:
    settings = get_settings()
    configured_users = [
        ("Local Admin", settings.dev_admin_email, settings.dev_admin_password, UserRole.ADMIN),
        ("Local Recruiter", settings.dev_recruiter_email, settings.dev_recruiter_password, UserRole.RECRUITER),
        ("Local Hiring Manager", settings.dev_manager_email, settings.dev_manager_password, UserRole.HIRING_MANAGER),
    ]

    async with AsyncSessionLocal() as session:
        repo = UserRepository(session)
        created = 0
        for name, email, password, role in configured_users:
            if not email or not password:
                continue
            await repo.upsert_dev_user(
                name=name,
                email=email,
                password_hash=hash_password(password),
                role=role,
            )
            created += 1
            print(f"Seeded {role.value}: {email.strip().lower()}")

    if created == 0:
        print("No dev users configured. Set DEV_*_EMAIL and DEV_*_PASSWORD environment variables.")


if __name__ == "__main__":
    asyncio.run(main())
