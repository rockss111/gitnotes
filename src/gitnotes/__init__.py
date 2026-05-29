"""
GitNotes Core Module
Provides initialization, editor configuration, and session management.
"""

from .init_cmd import init_repository
from .config_resolver import resolve_editor
from .session import Session, EditResult, SessionPaths
from .export import ExportResult, check_pandoc, export_note
from .search import SearchMatch, SearchResult, search_notes

__all__ = [
    "init_repository",
    "resolve_editor",
    "Session",
    "EditResult",
    "SessionPaths",
    "ExportResult",
    "check_pandoc",
    "export_note",
    "SearchMatch",
    "SearchResult",
    "search_notes",
]
