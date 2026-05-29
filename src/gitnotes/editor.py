"""
Editor Spawn & Session Lifecycle

Per ADR-0003 (Post-Editor Validation): exists, non-empty, UTF-8.
Per ADR-0004 (Change Detection): unified diff via Python difflib.
Per ADR-0006 (Git Commit): git add + git commit with meaningful message.
"""

import difflib
import subprocess
from pathlib import Path


def spawn_editor(editor_cmd: str, file_path: str) -> int:
    """
    Spawn an external editor as a child process and wait for it to exit.

    Args:
        editor_cmd: The editor command to execute (e.g., "vim", "nano")
        file_path: Absolute path to the file to edit

    Returns:
        int: The editor's exit code
    """
    result = subprocess.run(
        [editor_cmd, file_path],
        check=False,
    )
    return result.returncode


def validate_note(file_path: str) -> bool:
    """
    Validate a note file after editing.

    Checks:
        1. File exists
        2. File is non-empty
        3. File is valid UTF-8 (first 4KB)

    Args:
        file_path: Absolute path to the note file

    Returns:
        True if all checks pass, False otherwise
    """
    path = Path(file_path)
    if not path.exists():
        return False
    if path.stat().st_size == 0:
        return False
    try:
        with open(path, "rb") as f:
            chunk = f.read(4096)
        chunk.decode("utf-8")
        return True
    except (UnicodeDecodeError, OSError):
        return False


def detect_external_change(name: str) -> bool:
    """
    Check whether the note file was modified externally since the snapshot.

    Args:
        name: The note name (e.g., "my-note.md")

    Returns:
        True if the file differs from its snapshot (external change detected)
    """
    from .snapshot import snapshot_changed
    return snapshot_changed(name)


def edit_note(
    name: str,
    editor_cmd: str,
    on_external_change: callable = None,
    on_empty: callable = None,
    on_deleted: callable = None,
    _after_snapshot: callable = None,
) -> bool:
    """
    Full editing session lifecycle with external change detection and edge cases.

    Per ADR-0005:
    1. Acquire session lock
    2. Create pre-edit snapshot
    3. Check for external changes (pre-edit)
    4. Spawn editor and wait
    5. Handle empty/deleted file edge cases
    6. Validate post-edit file
    7. Compare hashes, show diff if changed
    8. Commit if user accepts, or revert

    Args:
        name: The note name (e.g., "my-note.md")
        editor_cmd: The editor command to spawn
        on_external_change: Callback invoked when external change detected.
            Receives (name, diff). Returns "accept", "retry", or "abort".
        on_empty: Callback when file is empty after edit.
            Receives (name, diff). Returns "keep" or "restore".
        on_deleted: Callback when file is missing after edit.
            Receives (name). Returns "restore" or "skip".

    Returns:
        True if changes were committed, False otherwise
    """
    from .session_manager import acquire_lock, release_lock
    from .snapshot import create_snapshot, snapshot_changed

    acquire_lock(name)
    try:
        create_snapshot(name)

        if _after_snapshot:
            _after_snapshot()

        if detect_external_change(name):
            if on_external_change:
                diff = get_diff(name)
                action = on_external_change(name, diff)
                if action == "retry":
                    _restore_snapshot(name)
                elif action == "accept":
                    pass
                else:
                    return False
            else:
                return False

        spawn_editor(editor_cmd, str(Path.cwd() / name))

        note_path = Path.cwd() / name
        if not note_path.exists():
            if on_deleted:
                action = on_deleted(name)
                if action == "restore":
                    _restore_snapshot(name)
            return False
        elif note_path.stat().st_size == 0:
            if on_empty:
                diff = get_diff(name)
                action = on_empty(name, diff)
                if action == "restore":
                    _restore_snapshot(name)
            return False
        elif not validate_note(str(note_path)):
            return False

        if not snapshot_changed(name):
            return False

        commit_note(name)
        return True
    finally:
        release_lock(name)


def _restore_snapshot(name: str) -> None:
    """Restore note content from its pre-edit snapshot."""
    repo_path = Path.cwd()
    sessions_dir = repo_path / ".gitnotes" / "sessions"
    snapshot_path = sessions_dir / f"{name}.pre-edit"
    note_path = repo_path / name
    if snapshot_path.exists():
        note_path.write_bytes(snapshot_path.read_bytes())


def commit_note(name: str) -> bool:
    """
    Commit a note file to Git if it has changed since the snapshot.

    Per ADR-0006: git add <file> + git commit -m "edit: <name>"

    Args:
        name: The note name (e.g., "my-note.md")

    Returns:
        True if a commit was made, False if skipped (unchanged)
    """
    from .snapshot import snapshot_changed

    if not snapshot_changed(name):
        return False

    repo_path = Path.cwd()
    note_path = repo_path / name

    subprocess.run(["git", "add", str(note_path)], check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", f"edit: {name}"],
        check=True, capture_output=True,
    )
    return True


def get_diff(name: str) -> str:
    """
    Compute unified diff between snapshot and current note content.

    Args:
        name: The note name (e.g., "my-note.md")

    Returns:
        str: Unified diff string, or empty string if no changes
    """
    repo_path = Path.cwd()
    sessions_dir = repo_path / ".gitnotes" / "sessions"
    snapshot_path = sessions_dir / f"{name}.pre-edit"
    note_path = repo_path / name

    if not snapshot_path.exists():
        return ""

    before = snapshot_path.read_text(encoding="utf-8")
    after = note_path.read_text(encoding="utf-8")

    if before == after:
        return ""

    diff = difflib.unified_diff(
        before.splitlines(keepends=True),
        after.splitlines(keepends=True),
        fromfile=f"a/{name}",
        tofile=f"b/{name}",
    )
    return "".join(diff)
