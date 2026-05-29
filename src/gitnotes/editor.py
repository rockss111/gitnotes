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
