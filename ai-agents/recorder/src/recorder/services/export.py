"""Export service — Markdown and PDF export of understanding documents and briefings."""

# Implementation: Phase 6
# Skeleton only.

from pathlib import Path

from recorder.core.config import settings


async def export_understanding_doc(session_id: str, format: str = "markdown") -> Path:
    """Export the shared understanding document to markdown or pdf.

    format: "markdown" | "pdf"
    Returns path to the exported file.
    Phase 6 implementation.
    """
    raise NotImplementedError("Document export — Phase 6")


async def export_briefing(persona_id: str, session_id: str, format: str = "markdown") -> Path:
    """Export a persona briefing to markdown or pdf.
    Phase 6 implementation.
    """
    raise NotImplementedError("Briefing export — Phase 6")
