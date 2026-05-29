"""
Tests for Slice 2a: Session Snapshot Protocol & Locking.

Per ADR-0001 (Snapshot Protocol): SHA256 hash + pre-edit snapshot file.
Per ADR-0002 (Session Locking): flock-based advisory locking.
"""

import hashlib
import os
import subprocess
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def repo_dir():
    saved_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        os.chdir(repo_path)
        subprocess.run(["git", "init"], check=True, capture_output=True)
        yield repo_path
    os.chdir(saved_cwd)


class TestSnapshotProtocol:
    """Slice 2a, first behavior: pre-edit snapshot via SHA256."""

    def test_creates_snapshot_file_with_content_and_returns_hash(self, repo_dir):
        """Create snapshot of a note, verify .pre-edit file and hash."""
        from src.gitnotes.snapshot import create_snapshot

        content = b"# Hello\n\nTest note.\n"
        note_path = repo_dir / "test-note.md"
        note_path.write_bytes(content)

        result = create_snapshot("test-note.md")

        snapshot_path = (
            repo_dir / ".gitnotes" / "sessions" / "test-note.md.pre-edit"
        )
        assert snapshot_path.exists()
        assert snapshot_path.read_bytes() == content

        assert result == hashlib.sha256(content).hexdigest()

    def test_detects_when_note_has_changed(self, repo_dir):
        """snapshot_changed returns True when content differs from snapshot."""
        from src.gitnotes.snapshot import create_snapshot, snapshot_changed

        note_path = repo_dir / "test-note.md"
        note_path.write_text("original content\n")

        create_snapshot("test-note.md")

        assert not snapshot_changed("test-note.md"), \
            "Should report no change before modification"

        note_path.write_text("modified content\n")

        assert snapshot_changed("test-note.md"), \
            "Should report change after modification"


class TestSessionLocking:
    """Slice 2a: Session Locking Protocol (ADR-0002)."""

    def test_exclusive_lock_prevents_concurrent_acquire(self, repo_dir):
        """Acquiring a lock on an already-locked name should fail."""
        from src.gitnotes.session_manager import acquire_lock, release_lock

        lock1 = acquire_lock("test-note.md")

        import pytest
        with pytest.raises(Exception):
            acquire_lock("test-note.md")

        release_lock("test-note.md")

    def test_lock_can_be_released_and_reacquired(self, repo_dir):
        """After release, the same lock can be acquired again."""
        from src.gitnotes.session_manager import acquire_lock, release_lock

        acquire_lock("test-note.md")
        release_lock("test-note.md")

        acquire_lock("test-note.md")
        release_lock("test-note.md")
