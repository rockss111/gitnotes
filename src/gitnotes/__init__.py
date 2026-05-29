"""
GitNotes Core Module
Provides initialization, editor configuration, and session management.
"""

from .init_cmd import init_repository
from .config_resolver import resolve_editor
from .session_manager import acquire_lock, release_lock
from .snapshot import create_snapshot, snapshot_changed

__all__ = [
    "init_repository",
    "resolve_editor", 
    "acquire_lock",
    "release_lock",
    "create_snapshot",
    "snapshot_changed",
]
