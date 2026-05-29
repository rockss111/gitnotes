"""
GitNotes Core Module
Provides initialization, editor configuration, and session management.
"""

from .init_cmd import init_repository
from .config_resolver import resolve_editor
from .session_manager import acquire_lock, release_lock
from .snapshot import create_snapshot, snapshot_changed
from .editor import spawn_editor, validate_note, edit_note, commit_note, get_diff
from .export import check_pandoc, export_note
from .search import search_notes

__all__ = [
    "init_repository",
    "resolve_editor", 
    "acquire_lock",
    "release_lock",
    "create_snapshot",
    "snapshot_changed",
    "spawn_editor",
    "validate_note",
    "edit_note",
    "commit_note",
    "get_diff",
    "check_pandoc",
    "export_note",
    "search_notes",
]
