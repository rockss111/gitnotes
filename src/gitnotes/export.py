"""
Pandoc Export

Per ADR-0008:
- pandoc file.md -o file.html
- Pre-flight: shutil.which("pandoc")
- Post-check: exit code + stderr
"""

import shutil
import subprocess
from pathlib import Path


def check_pandoc(pandoc_path: str = "pandoc") -> bool:
    """
    Check whether pandoc (or a compatible converter) is available.

    Args:
        pandoc_path: Path or name of the pandoc executable

    Returns:
        True if the executable exists and is runnable
    """
    return shutil.which(pandoc_path) is not None


def export_note(name: str, pandoc_path: str = "pandoc") -> bool:
    """
    Export a markdown note to HTML using pandoc.

    Args:
        name: The note name (e.g., "my-note.md")
        pandoc_path: Path or name of the pandoc executable

    Returns:
        True if export succeeded, False otherwise
    """
    if not check_pandoc(pandoc_path):
        return False

    repo_path = Path.cwd()
    note_path = repo_path / name
    html_path = note_path.with_suffix(".html")

    result = subprocess.run(
        [pandoc_path, str(note_path), "-o", str(html_path)],
        capture_output=True, text=True,
    )
    return result.returncode == 0
