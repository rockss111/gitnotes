"""
Unit Tests: Initialization component testing

Per ADR 0014 (Testability): Unit tests for isolated components like
hashing, config resolution, and lock management.
"""

import os
from pathlib import Path
import subprocess


class TestInitComponents:
    """Unit tests: Isolated initialization component testing."""

    def test_ensure_git_initialized_already_init(self):
        """Test that _ensure_git_initialized handles already-initialized repos."""
        from src.gitnotes.init_cmd import _ensure_git_initialized, _create_gitnotes_structure, _commit_initialization
        
        # Create a temp repo that's already initialized
        tmpdir = Path("/tmp/test-init-repo")
        tmpdir.mkdir(exist_ok=True)
        os.chdir(tmpdir)
        subprocess.run(["git", "init"], check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], check=True)
        
        # Should not raise
        _ensure_git_initialized(tmpdir)
    
    def test_create_gitnotes_structure(self):
        """Test that structure is created correctly."""
        from src.gitnotes.init_cmd import _create_gitnotes_structure
        
        tmpdir = Path("/tmp/test-structure-repo")
        tmpdir.mkdir(exist_ok=True)
        os.chdir(tmpdir)
        subprocess.run(["git", "init"], check=True, capture_output=True)
        
        # Should create directories without raising
        _create_gitnotes_structure(tmpdir)
        
        assert (tmpdir / ".gitnotes").is_dir()
        assert (tmpdir / ".gitnotes" / "config").exists()
        assert (tmpdir / ".gitnotes" / "sessions").is_dir()
    
    def test_create_gitattributes(self):
        """Test that .gitattributes is created with correct content."""
        from src.gitnotes.init_cmd import _create_gitattributes
        
        tmpdir = Path("/tmp/test-attrs-repo")
        tmpdir.mkdir(exist_ok=True)
        os.chdir(tmpdir)
        subprocess.run(["git", "init"], check=True, capture_output=True)
        
        # Should create file without raising
        _create_gitattributes(tmpdir)
        
        attrs_file = tmpdir / ".gitattributes"
        assert attrs_file.exists()
        content = attrs_file.read_text().strip()
        assert content == "*.md text eol=lf"
    
    def test_commit_initialization(self):
        """Test that commit works and creates correct message."""
        from src.gitnotes.init_cmd import _commit_initialization
        
        tmpdir = Path("/tmp/test-commit-repo")
        tmpdir.mkdir(exist_ok=True)
        os.chdir(tmpdir)
        subprocess.run(["git", "init"], check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], check=True)
        
        # Create some files to commit
        (tmpdir / ".gitnotes").mkdir()
        (tmpdir / ".gitnotes" / "config").touch()
        (tmpdir / ".gitattributes").write_text("*.md text eol=lf\n")
        
        # Should create commit without raising
        _commit_initialization(tmpdir)
        
        # Verify commit message
        result = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            capture_output=True,
            text=True
        )
        assert "Initialized GitNotes" in result.stdout
    
    def test_full_init_flow(self):
        """Test complete initialization flow."""
        from src.gitnotes.init_cmd import init_repository
        
        tmpdir = Path("/tmp/test-full-repo")
        tmpdir.mkdir(exist_ok=True)
        os.chdir(tmpdir)
        subprocess.run(["git", "init"], check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], check=True)
        
        # Run full init
        init_repository()
        
        # Verify all components exist
        assert (tmpdir / ".git").is_dir(), ".git/ should exist"
        assert (tmpdir / ".gitnotes" / "config").exists(), ".gitnotes/config should exist"
        assert (tmpdir / ".gitnotes" / "sessions").is_dir(), ".gitnotes/sessions/ should exist"
        attrs = tmpdir / ".gitattributes"
        assert attrs.exists()
        assert attrs.read_text().strip() == "*.md text eol=lf", \
            f".gitattributes content: {attrs.read_text()}"
        
        # Verify commit
        result = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            capture_output=True,
            text=True
        )
        assert "Initialized GitNotes" in result.stdout
