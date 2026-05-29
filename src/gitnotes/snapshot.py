"""
Session Snapshot Protocol

Per ADR-0001:
- Hash: SHA256 of file.md before/after edit
- Snapshot: .gitnotes/sessions/<name>.pre-edit stores full pre-edit content
"""

import hashlib
from pathlib import Path


def create_snapshot(name: str) -> str:
    """
    Create a pre-edit snapshot of a note file.

    Args:
        name: The note name (e.g., "my-note.md")

    Returns:
        str: SHA256 hex digest of the pre-edit content

    Side effects:
        Writes full content to .gitnotes/sessions/<name>.pre-edit
    """
    repo_path = Path.cwd()
    note_path = repo_path / name
    content = note_path.read_bytes()

    sessions_dir = repo_path / ".gitnotes" / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)

    snapshot_path = sessions_dir / f"{name}.pre-edit"
    snapshot_path.write_bytes(content)

    return hashlib.sha256(content).hexdigest()


def snapshot_changed(name: str) -> bool:
    """
    Check whether the current note content differs from its snapshot.

    Args:
        name: The note name (e.g., "my-note.md")

    Returns:
        True if the current content differs from the snapshot,
        False if they are identical.
    """
    repo_path = Path.cwd()
    note_path = repo_path / name
    sessions_dir = repo_path / ".gitnotes" / "sessions"
    snapshot_path = sessions_dir / f"{name}.pre-edit"

    if not snapshot_path.exists():
        return True

    current_hash = hashlib.sha256(note_path.read_bytes()).hexdigest()
    snapshot_hash = hashlib.sha256(snapshot_path.read_bytes()).hexdigest()

    return current_hash != snapshot_hash
