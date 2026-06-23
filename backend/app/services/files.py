from __future__ import annotations

import hashlib
from pathlib import Path
from uuid import UUID

from fastapi import UploadFile

from app.core.config import get_settings


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


async def save_resume_upload(job_id: UUID, candidate_id: UUID, upload: UploadFile) -> tuple[str, str]:
    content = await upload.read()
    digest = sha256_bytes(content)
    suffix = Path(upload.filename or "resume.bin").suffix or ".bin"
    settings = get_settings()
    folder = settings.data_dir / "resumes" / str(job_id)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{candidate_id}{suffix}"
    path.write_bytes(content)
    return str(path), digest

