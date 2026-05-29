"""
Repository Initialization

Per ADR 0011 (Initialization):
- git init if not already initialized
- Create .gitnotes/ directory with subdirectories:
  - .gitnotes/config (user preferences)
  - .gitnotes/sessions/ (pre-edit snapshots & locks)
- Write initial config file to .gitnotes/config
- Add .gitattributes with *.md text eol=lf
- Commit everything with message: "Initialized GitNotes"
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path


def _ensure_git_initialized(repo_path: Path) -> None:
    """Run git init if not already initialized."""
    try:
        result = subprocess.run(
            ["git", "status"],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        # If we get here without error, git is initialized
        if result.returncode == 0:
            return
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    
    subprocess.run(
        ["git", "init"],
        cwd=repo_path,
        check=True
    )


def _create_gitnotes_structure(repo_path: Path) -> None:
    """Create .gitnotes/ directory with subdirectories."""
    gitnotes_dir = repo_path / ".gitnotes"
    gitnotes_dir.mkdir(parents=True, exist_ok=True)
    
    config_file = gitnotes_dir / "config"
    if not config_file.exists():
        config_file.write_text(json.dumps({"editor": ""}))
    
    sessions_dir = gitnotes_dir / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)


def _create_gitattributes(repo_path: Path) -> None:
    """Add .gitattributes with *.md text eol=lf."""
    gitattributes_file = repo_path / ".gitattributes"
    if not gitattributes_file.exists():
        gitattributes_file.write_text("*.md text eol=lf\n")


def _commit_initialization(repo_path: Path) -> None:
    """Commit everything with message: 'Initialized GitNotes'."""
    # Add all files
    subprocess.run(
        ["git", "add", ".gitnotes", ".gitattributes"],
        cwd=repo_path,
        check=True
    )
    
    # Commit with specific message
    subprocess.run(
        [
            "git", "commit", "-m", "Initialized GitNotes"
        ],
        cwd=repo_path,
        check=True
    )


def init_repository() -> None:
    """
    Initialize a new GitNotes repository.
    
    Bootstraps a new GitNotes repo by initializing Git, creating necessary
    directories, and setting up configuration. See ADR 0011 for details.
    
    Steps:
    1. Run git init if not already initialized
    2. Create .gitnotes/ directory with subdirectories:
       - .gitnotes/config (user preferences)
       - .gitnotes/sessions/ (pre-edit snapshots & locks)
    3. Write initial config file to .gitnotes/config
    4. Add .gitattributes with *.md text eol=lf
    5. Commit everything with message: "Initialized GitNotes"
    
    Raises:
        subprocess.SubprocessError: If any git command fails
    """
    # Get current working directory as repo path
    repo_path = Path.cwd()
    
    _ensure_git_initialized(repo_path)

    gitnotes_config = repo_path / ".gitnotes" / "config"
    if gitnotes_config.exists():
        return

    _create_gitnotes_structure(repo_path)
    _create_gitattributes(repo_path)
    _commit_initialization(repo_path)
