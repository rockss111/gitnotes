"""
GitNotes Core Module
Provides initialization, editor configuration, and session management.
"""

from .init_cmd import init_repository
from .config_resolver import resolve_editor
from .session import Session, EditResult, SessionPaths
from .export import check_pandoc, export_note
from .search import search_notes

__all__ = [
    "init_repository",
    "resolve_editor",
    "Session",
    "EditResult",
    "SessionPaths",
    "check_pandoc",
    "export_note",
    "search_notes",
]
