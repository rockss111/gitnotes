"""
Tests for the deepened Session module.

Covers:
- Session init: snapshot creation, lock acquisition
- check_external_change / restore
- edit() lifecycle: UNCHANGED, CHANGED, EMPTY, DELETED, INVALID
- diff() display
- commit() integration
- Lock contention and release
- Export and Search (unchanged from previous)
"""

import hashlib
import os
import subprocess
import tempfile
from pathlib import Path

import pytest
from src.gitnotes.session import SessionPaths


@pytest.fixture
def repo_dir():
    saved_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        os.chdir(repo_path)
        subprocess.run(["git", "init"], check=True, capture_output=True)
        yield repo_path
    os.chdir(saved_cwd)


def _config_git_user(repo_dir):
    subprocess.run(
        ["git", "config", "user.email", "test@gitnotes.dev"],
        check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "GitNotes Test"],
        check=True, capture_output=True,
    )


class TestSessionInit:
    """Session construction: lock acquire + snapshot creation."""

    def test_creates_snapshot_and_lock_files(self, repo_dir):
        from src.gitnotes.session import Session

        content = b"# Hello\n\nTest note.\n"
        note_path = repo_dir / "test-note.md"
        note_path.write_bytes(content)

        session = Session("test-note.md", repo_dir)

        p = SessionPaths.for_note(repo_dir, "test-note.md")

        assert p.snapshot.exists()
        assert p.snapshot.read_bytes() == content
        assert p.lock.exists()

        session.close()

    def test_snapshot_stores_pre_edit_hash(self, repo_dir):
        from src.gitnotes.session import Session

        content = b"original content\n"
        note_path = repo_dir / "test-note.md"
        note_path.write_bytes(content)

        session = Session("test-note.md", repo_dir)
        expected_hash = hashlib.sha256(content).hexdigest()
        assert session._pre_edit_hash == expected_hash

        session.close()


class TestExternalChange:
    """check_external_change and restore."""

    def test_detects_external_change(self, repo_dir):
        from src.gitnotes.session import Session

        note_path = repo_dir / "test-note.md"
        note_path.write_text("original\n")

        with Session("test-note.md", repo_dir) as s:
            assert not s.check_external_change()
            note_path.write_text("externally modified\n")
            assert s.check_external_change()

    def test_restore_reverts_external_change(self, repo_dir):
        from src.gitnotes.session import Session

        note_path = repo_dir / "test-note.md"
        note_path.write_text("original\n")

        with Session("test-note.md", repo_dir) as s:
            note_path.write_text("externally modified\n")
            s.restore()
            assert note_path.read_text() == "original\n"


class TestSessionEdit:
    """edit() lifecycle: every EditResult path."""

    def test_unchanged_with_true_editor(self, repo_dir):
        from src.gitnotes.session import Session, EditResult

        note_path = repo_dir / "test-note.md"
        note_path.write_text("content\n")

        with Session("test-note.md", repo_dir) as s:
            result = s.edit("true")
            assert result == EditResult.UNCHANGED

    def test_changed_with_modifying_script(self, repo_dir):
        from src.gitnotes.session import Session, EditResult

        note_path = repo_dir / "test-note.md"
        note_path.write_text("original\n")

        modify_script = repo_dir / "modify_editor.sh"
        modify_script.write_text("#!/bin/sh\necho 'modified' > \"$1\"\n")
        modify_script.chmod(0o755)

        with Session("test-note.md", repo_dir) as s:
            result = s.edit(str(modify_script))
            assert result == EditResult.CHANGED

    def test_empty_returns_empty(self, repo_dir):
        from src.gitnotes.session import Session, EditResult

        note_path = repo_dir / "test-note.md"
        note_path.write_text("original content\n")

        empty_script = repo_dir / "empty_editor.sh"
        empty_script.write_text("#!/bin/sh\n: > \"$1\"\n")
        empty_script.chmod(0o755)

        with Session("test-note.md", repo_dir) as s:
            result = s.edit(str(empty_script))
            assert result == EditResult.EMPTY

    def test_deleted_returns_deleted(self, repo_dir):
        from src.gitnotes.session import Session, EditResult

        note_path = repo_dir / "test-note.md"
        note_path.write_text("original content\n")

        delete_script = repo_dir / "delete_editor.sh"
        delete_script.write_text("#!/bin/sh\nrm \"$1\"\n")
        delete_script.chmod(0o755)

        with Session("test-note.md", repo_dir) as s:
            result = s.edit(str(delete_script))
            assert result == EditResult.DELETED

    def test_invalid_utf8_returns_invalid(self, repo_dir):
        from src.gitnotes.session import Session, EditResult

        note_path = repo_dir / "test-note.md"
        note_path.write_text("original\n")

        bad_utf8_script = repo_dir / "bad_utf8_editor.sh"
        bad_utf8_script.write_text("#!/bin/sh\nprintf '\\xff\\xfe' > \"$1\"\n")
        bad_utf8_script.chmod(0o755)

        with Session("test-note.md", repo_dir) as s:
            result = s.edit(str(bad_utf8_script))
            assert result == EditResult.INVALID


class TestDiffDisplay:
    """diff() — unified diff output (ADR-0004)."""

    def test_returns_unified_diff_when_content_changed(self, repo_dir):
        from src.gitnotes.session import Session

        note_path = repo_dir / "test-note.md"
        note_path.write_text("line one\nline two\nline three\n")

        modify_script = repo_dir / "modify_editor.sh"
        modify_script.write_text(
            "#!/bin/sh\ncat > \"$1\" << 'EOF'\nline one\nline two modified\nline three\nEOF\n"
        )
        modify_script.chmod(0o755)

        with Session("test-note.md", repo_dir) as s:
            s.edit(str(modify_script))
            diff = s.diff()
            assert isinstance(diff, str)
            assert len(diff) > 0
            assert "-line two" in diff or "-line two" in diff
            assert "+line two modified" in diff

    def test_returns_empty_when_unchanged(self, repo_dir):
        from src.gitnotes.session import Session

        note_path = repo_dir / "test-note.md"
        note_path.write_text("fixed content\n")

        with Session("test-note.md", repo_dir) as s:
            s.edit("true")
            assert s.diff() == ""


class TestGitCommit:
    """commit() — git integration (ADR-0006)."""

    def test_commits_changed_note_with_edit_message(self, repo_dir):
        from src.gitnotes.session import Session, EditResult

        _config_git_user(repo_dir)

        note_path = repo_dir / "test-note.md"
        note_path.write_text("initial\n")
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], check=True, capture_output=True)

        modify_script = repo_dir / "modify_editor.sh"
        modify_script.write_text("#!/bin/sh\necho 'modified' > \"$1\"\n")
        modify_script.chmod(0o755)

        with Session("test-note.md", repo_dir) as s:
            s.edit(str(modify_script))
            s.commit()

        result = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            capture_output=True, text=True, check=True,
        )
        assert "edit:" in result.stdout

    def test_does_not_commit_unchanged_note(self, repo_dir):
        from src.gitnotes.session import Session

        _config_git_user(repo_dir)

        note_path = repo_dir / "test-note.md"
        note_path.write_text("same\n")
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], check=True, capture_output=True)

        with Session("test-note.md", repo_dir) as s:
            s.commit()

        result = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            capture_output=True, text=True, check=True,
        )
        assert "initial" in result.stdout
        assert "edit:" not in result.stdout


class TestSessionRestore:
    """restore() for empty and deleted edge cases."""

    def test_restores_empty_file_from_snapshot(self, repo_dir):
        from src.gitnotes.session import Session, EditResult

        note_path = repo_dir / "test-note.md"
        note_path.write_text("original content\n")

        empty_script = repo_dir / "empty_editor.sh"
        empty_script.write_text("#!/bin/sh\n: > \"$1\"\n")
        empty_script.chmod(0o755)

        with Session("test-note.md", repo_dir) as s:
            result = s.edit(str(empty_script))
            assert result == EditResult.EMPTY
            s.restore()
            assert note_path.read_text() == "original content\n"

    def test_restores_deleted_file_from_snapshot(self, repo_dir):
        from src.gitnotes.session import Session, EditResult

        note_path = repo_dir / "test-note.md"
        note_path.write_text("original content\n")

        delete_script = repo_dir / "delete_editor.sh"
        delete_script.write_text("#!/bin/sh\nrm \"$1\"\n")
        delete_script.chmod(0o755)

        with Session("test-note.md", repo_dir) as s:
            result = s.edit(str(delete_script))
            assert result == EditResult.DELETED
            s.restore()
            assert note_path.read_text() == "original content\n"


class TestSessionLocking:
    """Lock contention and lifecycle (ADR-0002)."""

    def test_exclusive_lock_prevents_concurrent_session(self, repo_dir):
        from src.gitnotes.session import Session

        note_path = repo_dir / "test-note.md"
        note_path.write_text("content\n")

        session1 = Session("test-note.md", repo_dir)

        with pytest.raises(OSError):
            Session("test-note.md", repo_dir)

        session1.close()

    def test_lock_can_be_released_and_reacquired(self, repo_dir):
        from src.gitnotes.session import Session

        note_path = repo_dir / "test-note.md"
        note_path.write_text("content\n")

        session1 = Session("test-note.md", repo_dir)
        session1.close()

        session2 = Session("test-note.md", repo_dir)
        session2.close()

    def test_context_manager_releases_lock(self, repo_dir):
        from src.gitnotes.session import Session

        note_path = repo_dir / "test-note.md"
        note_path.write_text("content\n")

        with Session("test-note.md", repo_dir) as s:
            pass

        with Session("test-note.md", repo_dir) as s:
            pass


class TestExport:
    """Slice 5: Pandoc Export (ADR-0008)."""

    def test_preflight_returns_false_when_pandoc_missing(self, repo_dir):
        from src.gitnotes.export import check_pandoc

        assert not check_pandoc("nonexistent-pandoc")

    def test_preflight_accepts_custom_pandoc_path(self, repo_dir):
        from src.gitnotes.export import check_pandoc

        assert check_pandoc("true")

    def test_export_returns_true_on_success(self, repo_dir):
        from src.gitnotes.export import export_note

        note_path = repo_dir / "test-note.md"
        note_path.write_text("# Hello\n")
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "add"], check=True, capture_output=True)

        assert export_note("test-note.md", "true") is True

    def test_export_returns_false_on_failure(self, repo_dir):
        from src.gitnotes.export import export_note

        note_path = repo_dir / "test-note.md"
        note_path.write_text("# Hello\n")
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "add"], check=True, capture_output=True)

        assert export_note("test-note.md", "false") is False

    def test_export_skips_when_pandoc_missing(self, repo_dir):
        from src.gitnotes.export import export_note

        note_path = repo_dir / "test-note.md"
        note_path.write_text("# Hello\n")

        assert export_note("test-note.md", "nonexistent-pandoc") is False


class TestSearch:
    """Slice 5: Search Command (ADR-0009)."""

    def test_search_returns_empty_when_no_matches(self, repo_dir):
        from src.gitnotes.search import search_notes

        note_path = repo_dir / "test-note.md"
        note_path.write_text("hello world\n")
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "add note"], check=True, capture_output=True)

        results = search_notes("nonexistent")
        assert results == ""

    def test_search_finds_matching_content(self, repo_dir):
        from src.gitnotes.search import search_notes

        note_path = repo_dir / "test-note.md"
        note_path.write_text("hello world\nfoo bar\n")
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "add note"], check=True, capture_output=True)

        results = search_notes("hello")
        assert "test-note.md" in results
        assert "hello" in results

    def test_search_case_insensitive(self, repo_dir):
        from src.gitnotes.search import search_notes

        note_path = repo_dir / "test-note.md"
        note_path.write_text("HELLO world\n")
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "add note"], check=True, capture_output=True)

        results = search_notes("hello")
        assert "HELLO" in results
