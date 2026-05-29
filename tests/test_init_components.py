"""
Unit Tests: Initialization component testing

Per ADR 0014 (Testability): Unit tests for isolated components like
hashing, config resolution, and lock management.
"""

import os
import subprocess
import tempfile
from pathlib import Path


class TestInitComponents:
    """Unit tests: Isolated initialization component testing."""

    def _setup_temp_repo(self):
        """Create a temp dir, chdir into it, init git, and configure user."""
        saved_cwd = os.getcwd()
        tmpdir = tempfile.mkdtemp()
        repo_path = Path(tmpdir)
        os.chdir(repo_path)
        subprocess.run(["git", "init"], check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            check=True, capture_output=True,
        )
        return repo_path, saved_cwd

    def test_ensure_git_initialized_already_init(self):
        """Test that _ensure_git_initialized handles already-initialized repos."""
        from src.gitnotes.init_cmd import _ensure_git_initialized

        repo_path, saved_cwd = self._setup_temp_repo()

        try:
            _ensure_git_initialized(repo_path)
        finally:
            os.chdir(saved_cwd)

    def test_create_gitnotes_structure(self):
        """Test that structure is created correctly."""
        from src.gitnotes.init_cmd import _create_gitnotes_structure

        repo_path, saved_cwd = self._setup_temp_repo()

        try:
            _create_gitnotes_structure(repo_path)

            assert (repo_path / ".gitnotes").is_dir()
            assert (repo_path / ".gitnotes" / "config").exists()
            assert (repo_path / ".gitnotes" / "sessions").is_dir()
        finally:
            os.chdir(saved_cwd)

    def test_create_gitattributes(self):
        """Test that .gitattributes is created with correct content."""
        from src.gitnotes.init_cmd import _create_gitattributes

        repo_path, saved_cwd = self._setup_temp_repo()

        try:
            _create_gitattributes(repo_path)

            attrs_file = repo_path / ".gitattributes"
            assert attrs_file.exists()
            content = attrs_file.read_text().strip()
            assert content == "*.md text eol=lf"
        finally:
            os.chdir(saved_cwd)

    def test_commit_initialization(self):
        """Test that commit works and creates correct message."""
        from src.gitnotes.init_cmd import _commit_initialization

        repo_path, saved_cwd = self._setup_temp_repo()

        try:
            (repo_path / ".gitnotes").mkdir()
            (repo_path / ".gitnotes" / "config").touch()
            (repo_path / ".gitattributes").write_text("*.md text eol=lf\n")

            _commit_initialization(repo_path)

            result = subprocess.run(
                ["git", "log", "--oneline", "-1"],
                capture_output=True, text=True,
            )
            assert "Initialized GitNotes" in result.stdout
        finally:
            os.chdir(saved_cwd)

    def test_full_init_flow(self):
        """Test complete initialization flow."""
        from src.gitnotes.init_cmd import init_repository

        repo_path, saved_cwd = self._setup_temp_repo()

        try:
            init_repository()

            assert (repo_path / ".git").is_dir(), ".git/ should exist"
            assert (repo_path / ".gitnotes" / "config").exists(), \
                ".gitnotes/config should exist"
            assert (repo_path / ".gitnotes" / "sessions").is_dir(), \
                ".gitnotes/sessions/ should exist"
            attrs = repo_path / ".gitattributes"
            assert attrs.exists()
            assert attrs.read_text().strip() == "*.md text eol=lf", \
                f".gitattributes content: {attrs.read_text()}"

            result = subprocess.run(
                ["git", "log", "--oneline", "-1"],
                capture_output=True, text=True,
            )
            assert "Initialized GitNotes" in result.stdout
        finally:
            os.chdir(saved_cwd)
