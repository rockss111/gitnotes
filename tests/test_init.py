"""
Integration tests for FR-01 (Initialization Protocol).

All 6 acceptance criteria (FC-01.1 through FC-01.6) tested against
temporary repositories via the public init_repository() interface.

Per ADR 0014 (Testability): Integration-style tests against temp repos.
"""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest


def _ensure_global_git_config() -> None:
    subprocess.run(
        ["git", "config", "--global", "user.email", "test@gitnotes.dev"],
        check=True, capture_output=True
    )
    subprocess.run(
        ["git", "config", "--global", "user.name", "GitNotes Test"],
        check=True, capture_output=True
    )


@pytest.fixture
def repo_dir():
    _ensure_global_git_config()
    saved_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        os.chdir(repo_path)
        yield repo_path
    os.chdir(saved_cwd)


class TestInitRepository:
    """FR-01: Initialization Protocol (all 6 FCs via public interface)."""

    # ── FC-01.1: Creates .git/ directory if not present, idempotent ──

    def test_creates_git_directory(self, repo_dir):
        from src.gitnotes.init_cmd import init_repository
        init_repository()
        assert (repo_dir / ".git").is_dir()

    def test_idempotent(self, repo_dir):
        from src.gitnotes.init_cmd import init_repository
        init_repository()
        init_repository()
        assert (repo_dir / ".git").is_dir()

    # ── FC-01.2: Creates .gitnotes/config with default editor config ──

    def test_creates_config_file_with_editor_setting(self, repo_dir):
        from src.gitnotes.init_cmd import init_repository
        init_repository()
        config_file = repo_dir / ".gitnotes" / "config"
        assert config_file.is_file()
        content = config_file.read_text()
        assert "editor" in content

    # ── FC-01.3: Creates .gitnotes/sessions/ subdirectory ──

    def test_creates_sessions_directory(self, repo_dir):
        from src.gitnotes.init_cmd import init_repository
        init_repository()
        assert (repo_dir / ".gitnotes" / "sessions").is_dir()

    # ── FC-01.4: Writes .gitattributes with *.md text eol=lf ──

    def test_writes_gitattributes_with_correct_content(self, repo_dir):
        from src.gitnotes.init_cmd import init_repository
        init_repository()
        attrs_file = repo_dir / ".gitattributes"
        assert attrs_file.is_file()
        content = attrs_file.read_text().strip()
        assert content == "*.md text eol=lf"

    # ── FC-01.5: Adds all new files to Git staging ──

    def test_tracks_all_new_files_in_git(self, repo_dir):
        from src.gitnotes.init_cmd import init_repository
        init_repository()
        result = subprocess.run(
            ["git", "ls-files"], capture_output=True, text=True, check=True
        )
        tracked = result.stdout.splitlines()
        assert ".gitnotes/config" in tracked
        assert ".gitattributes" in tracked

    # ── FC-01.6: Creates initial commit with message "Initialized GitNotes" ──

    def test_creates_initial_commit_with_correct_message(self, repo_dir):
        from src.gitnotes.init_cmd import init_repository
        init_repository()
        result = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            capture_output=True, text=True, check=True
        )
        assert "Initialized GitNotes" in result.stdout
