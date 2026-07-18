"""Deterministic raw-text extraction from resume files. No OCR — text-based
PDF/DOCX only, per the build spec's edge-case constraints.
"""

import io

from docx import Document
from pypdf import PdfReader


class UnsupportedResumeFormat(ValueError):
    pass


def extract_text(filename: str, content: bytes) -> str:
    suffix = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if suffix == "pdf":
        return _extract_pdf(content)
    if suffix == "docx":
        return _extract_docx(content)
    raise UnsupportedResumeFormat(f"Unsupported resume file type: .{suffix or 'unknown'}")


def _extract_pdf(content: bytes) -> str:
    reader = PdfReader(io.BytesIO(content))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages).strip()


def _extract_docx(content: bytes) -> str:
    document = Document(io.BytesIO(content))
    paragraphs = [p.text for p in document.paragraphs]
    return "\n".join(paragraphs).strip()
