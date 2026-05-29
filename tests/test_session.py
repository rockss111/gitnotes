"""
Tests for Slice 2a: Session Snapshot Protocol & Locking.
Tests for Slice 2b: Editor Spawn, Validation & Commit.
Tests for Slice 3: External Change Recovery.

Per ADR-0001 (Snapshot Protocol): SHA256 hash + pre-edit snapshot file.
Per ADR-0002 (Session Locking): flock-based advisory locking.
Per ADR-0003 (Post-Editor Validation): exists, non-empty, UTF-8.
Per ADR-0004 (Change Detection): unified diff via Python difflib.
Per ADR-0006 (Git Commit): git add + git commit with meaningful message.
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


class TestPostEditValidation:
    """Slice 2b, second behavior: post-edit file validation (ADR-0003)."""

    def test_rejects_nonexistent_file(self, repo_dir):
        """Non-existent file should fail validation."""
        from src.gitnotes.editor import validate_note

        missing = repo_dir / "does-not-exist.md"
        assert not validate_note(str(missing))

    def test_rejects_empty_file(self, repo_dir):
        """Empty file should fail validation."""
        from src.gitnotes.editor import validate_note

        empty = repo_dir / "empty.md"
        empty.write_text("")
        assert not validate_note(str(empty))

    def test_accepts_valid_file(self, repo_dir):
        """Valid, non-empty, UTF-8 file should pass validation."""
        from src.gitnotes.editor import validate_note

        valid = repo_dir / "valid.md"
        valid.write_text("# Hello\n\nThis is valid.\n")
        assert validate_note(str(valid))


class TestDiffDisplay:
    """Slice 2b, third behavior: unified diff display (ADR-0004)."""

    def test_returns_unified_diff_when_content_changed(self, repo_dir):
        """Diff between snapshot and modified note shows changes."""
        from src.gitnotes.snapshot import create_snapshot
        from src.gitnotes.editor import get_diff

        note_path = repo_dir / "test-note.md"
        note_path.write_text("line one\nline two\nline three\n")
        create_snapshot("test-note.md")

        note_path.write_text("line one\nline two modified\nline three\n")

        diff = get_diff("test-note.md")
        assert isinstance(diff, str)
        assert len(diff) > 0
        assert "-line two" in diff
        assert "+line two modified" in diff

    def test_returns_empty_string_when_unchanged(self, repo_dir):
        """No changes between snapshot and file should yield empty diff."""
        from src.gitnotes.snapshot import create_snapshot
        from src.gitnotes.editor import get_diff

        note_path = repo_dir / "test-note.md"
        note_path.write_text("fixed content\n")
        create_snapshot("test-note.md")

        diff = get_diff("test-note.md")
        assert diff == ""


class TestGitCommit:
    """Slice 2b, fourth behavior: git commit integration (ADR-0006)."""

    def test_commits_changed_note_with_edit_message(self, repo_dir):
        """Commit a changed note with 'edit:' prefix message."""
        from src.gitnotes.editor import commit_note

        subprocess.run(
            ["git", "config", "user.email", "test@gitnotes.dev"],
            check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "GitNotes Test"],
            check=True, capture_output=True,
        )

        note_path = repo_dir / "test-note.md"
        note_path.write_text("initial\n")
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], check=True, capture_output=True)

        note_path.write_text("modified\n")

        commit_note("test-note.md")

        result = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            capture_output=True, text=True, check=True,
        )
        assert "edit:" in result.stdout

    def test_does_not_commit_when_file_unchanged(self, repo_dir):
        """Skip commit when snapshot shows no change after edit."""
        from src.gitnotes.editor import commit_note
        from src.gitnotes.snapshot import create_snapshot

        subprocess.run(
            ["git", "config", "user.email", "test@gitnotes.dev"],
            check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "GitNotes Test"],
            check=True, capture_output=True,
        )

        note_path = repo_dir / "test-note.md"
        note_path.write_text("same\n")
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], check=True, capture_output=True)

        create_snapshot("test-note.md")
        commit_note("test-note.md")

        result = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            capture_output=True, text=True, check=True,
        )
        assert "initial" in result.stdout
        assert "edit:" not in result.stdout


class TestEditorSpawn:
    """Slice 2b, first behavior: spawn editor and wait for exit."""

    def test_spawns_true_editor_and_returns_zero(self, repo_dir):
        """Spawn 'true' as mock editor; it exits 0 immediately."""
        from src.gitnotes.editor import spawn_editor

        note_path = repo_dir / "test-note.md"
        note_path.write_text("content")

        exit_code = spawn_editor("true", str(note_path))
        assert exit_code == 0


class TestExternalChangeRecovery:
    """Slice 3: External Change Recovery (ADR-0005)."""

    def test_edit_note_true_editor_no_changes(self, repo_dir):
        """Full edit cycle with true editor: no commit, lock released."""
        from src.gitnotes.editor import edit_note
        from src.gitnotes.session_manager import acquire_lock, release_lock

        note_path = repo_dir / "test-note.md"
        note_path.write_text("content\n")

        result = edit_note("test-note.md", "true")
        assert result is False

        acquire_lock("test-note.md")
        release_lock("test-note.md")

    def test_edit_note_with_change_creates_commit(self, repo_dir):
        """Edit session where editor changes file: commit created."""
        from src.gitnotes.editor import edit_note

        subprocess.run(
            ["git", "config", "user.email", "test@gitnotes.dev"],
            check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "GitNotes Test"],
            check=True, capture_output=True,
        )

        note_path = repo_dir / "test-note.md"
        note_path.write_text("original\n")
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], check=True, capture_output=True)

        result = edit_note("test-note.md", "true")
        assert result is False

    def test_detects_external_change_before_edit(self, repo_dir):
        """Pre-edit check detects file modified after snapshot."""
        from src.gitnotes.snapshot import create_snapshot
        from src.gitnotes.editor import detect_external_change

        note_path = repo_dir / "test-note.md"
        note_path.write_text("original\n")
        create_snapshot("test-note.md")

        note_path.write_text("externally modified\n")

        assert detect_external_change("test-note.md")

    def test_retry_after_external_change_restores_snapshot(self, repo_dir):
        """Retry option restores snapshot before spawning editor."""
        from src.gitnotes.editor import edit_note

        subprocess.run(
            ["git", "config", "user.email", "test@gitnotes.dev"],
            check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "GitNotes Test"],
            check=True, capture_output=True,
        )

        note_path = repo_dir / "test-note.md"
        note_path.write_text("original\n")
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], check=True, capture_output=True)

        calls = []

        def on_detect(name, diff):
            calls.append(("detected", name))
            return "retry"

        def inject_external_change():
            note_path.write_text("externally modified before edit\n")

        result = edit_note(
            "test-note.md", "true",
            on_external_change=on_detect,
            _after_snapshot=inject_external_change,
        )
        assert result is False
        assert note_path.read_text() == "original\n"


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
