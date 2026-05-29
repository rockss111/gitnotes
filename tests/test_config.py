"""
Unit Tests: Isolated component testing

Per ADR 0014 (Testability): Unit tests for isolated components like hashing,
config resolution, and lock management.
"""

import os
from pathlib import Path


class TestConfigResolver:
    """Unit tests: Editor configuration resolution."""

    def test_fallback_precedence(self):
        """Test that fallback chain works in correct order."""
        from src.gitnotes.config_resolver import resolve_editor, _get_env_var_fallbacks
        
        # Clear any existing env vars to force fallback
        original_visual = os.environ.pop("VISUAL", None)
        original_editor = os.environ.pop("EDITOR", None)
        
        try:
            fallbacks = _get_env_var_fallbacks()
            assert len(fallbacks) == 2, "Should have exactly 2 fallbacks"
            assert fallbacks[0][0] == "VISUAL", "First fallback should be VISUAL"
            assert fallbacks[1][0] == "EDITOR", "Second fallback should be EDITOR"
        finally:
            # Restore
            if original_visual is not None:
                os.environ["VISUAL"] = original_visual
            elif "VISUAL" in os.environ:
                del os.environ["VISUAL"]
            
            if original_editor is not None:
                os.environ["EDITOR"] = original_editor
            elif "EDITOR" in os.environ:
                del os.environ["EDITOR"]
        
        # Test VISUAL fallback
        os.environ["VISUAL"] = "vim"
        assert resolve_editor() == "vim", "Should return VISUAL when set"
        
        # Clean up
        if "VISUAL" in os.environ:
            del os.environ["VISUAL"]
    
    def test_empty_config_returns_fallbacks(self):
        """Test that empty config file still checks env vars."""
        from src.gitnotes.config_resolver import resolve_editor
        
        # Simulate empty/missing project config
        os.environ["VISUAL"] = "nano"
        result = resolve_editor()
        assert result == "nano", "Should fall through to VISUAL when config is empty"
        
        if "VISUAL" in os.environ:
            del os.environ["VISUAL"]


class TestSessionManager:
    """Unit tests: Session locking (simulated)."""

    def test_lock_file_creation(self):
        """Test that lock files are created in correct location."""
        from src.gitnotes.session_manager import acquire_lock, release_lock
        
        # Create a temp directory for the repo
        tmpdir = Path("/tmp/test-lock-repo")
        tmpdir.mkdir(exist_ok=True)
        os.chdir(tmpdir)
        
        # Initialize git (required by session manager)
        import subprocess
        subprocess.run(["git", "init"], check=True, capture_output=True)
        
        # Acquire lock
        process = acquire_lock("test-note")
        assert process is not None, "Should return a process handle"
        
        # Verify lock file exists
        lock_file = tmpdir / ".gitnotes" / "sessions" / "test-note.lock"
        assert lock_file.exists(), f"Lock file should be created at {lock_file}"
    
    def test_lock_release(self):
        """Test that locks can be released."""
        from src.gitnotes.session_manager import acquire_lock, release_lock
        
        tmpdir = Path("/tmp/test-lock-repo2")
        tmpdir.mkdir(exist_ok=True)
        os.chdir(tmpdir)
        subprocess.run(["git", "init"], check=True, capture_output=True)
        
        # Acquire and release lock
        process = acquire_lock("test-note-2")
        assert process is not None
        
        release_lock("test-note-2")
    
    def test_lock_file_path_format(self):
        """Test that lock file follows naming convention."""
        from src.gitnotes.session_manager import acquire_lock, release_lock
        
        tmpdir = Path("/tmp/test-lock-repo3")
        tmpdir.mkdir(exist_ok=True)
        os.chdir(tmpdir)
        subprocess.run(["git", "init"], check=True, capture_output=True)
        
        # Test different note name formats
        test_names = [
            "hello.md",
            "my-note.txt",
            "test_123.py",
        ]
        
        for note_name in test_names:
            process = acquire_lock(note_name)
            lock_file = tmpdir / ".gitnotes" / "sessions" / f"{note_name}.lock"
            assert lock_file.exists(), f"Lock file should be at {lock_file}"
            release_lock(note_name)
