from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader


def extract_text_from_file(path: str) -> str:
    file_path = Path(path)
    if file_path.suffix.lower() == ".pdf":
        reader = PdfReader(str(file_path))
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    return file_path.read_text(encoding="utf-8", errors="ignore").strip()

