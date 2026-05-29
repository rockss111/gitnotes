import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock

from click.testing import CliRunner
from src.gitnotes.cli import main
from src.gitnotes.config_resolver import ConfigNotResolvedError
from src.gitnotes.export import ExportResult
from src.gitnotes.init_cmd import InitializationError
from src.gitnotes.search import SearchResult, SearchMatch
from src.gitnotes.session import EditResult


class TestMainModule:
    def test_main_module_exists(self):
        assert Path("src/gitnotes/__main__.py").is_file()

    def test_python_m_gitnotes_exits_zero(self):
        result = subprocess.run(
            [sys.executable, "-m", "gitnotes", "--help"],
            capture_output=True, text=True,
            env={**os.environ, "PYTHONPATH": "src"},
        )
        assert result.returncode == 0

    def test_python_m_gitnotes_shows_init_command(self):
        result = subprocess.run(
            [sys.executable, "-m", "gitnotes", "--help"],
            capture_output=True, text=True,
            env={**os.environ, "PYTHONPATH": "src"},
        )
        assert "init" in result.stdout


class TestCliModule:
    def test_main_is_callable(self):
        assert callable(main)


class TestInitCli:
    def test_exit_0_on_success(self, tmp_path):
        subprocess.run(
            ["git", "config", "--global", "user.email", "test@gitnotes.dev"],
            check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "config", "--global", "user.name", "GitNotes Test"],
            check=True, capture_output=True,
        )
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(main, ["init"])
            assert result.exit_code == 0
            assert Path(".git").is_dir()
            assert Path(".gitnotes").is_dir()

    def test_exit_1_on_initialization_error(self, monkeypatch):
        def raise_error(*a, **kw):
            raise InitializationError("Git 'user.name' is not configured.")
        monkeypatch.setattr("src.gitnotes.cli.init_repository", raise_error)
        monkeypatch.setattr("shutil.which", lambda cmd: "/usr/bin/git")
        runner = CliRunner()
        result = runner.invoke(main, ["init"])
        assert result.exit_code == 1

    def test_exit_2_on_missing_git(self, monkeypatch):
        monkeypatch.setattr("shutil.which", lambda cmd: None)
        runner = CliRunner()
        result = runner.invoke(main, ["init"])
        assert result.exit_code == 2


class TestNewCli:
    def test_successful_creation(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.gitnotes.cli.resolve_editor", lambda: "vim")
        mock_session = MagicMock()
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = None
        mock_session.edit.return_value = EditResult.CHANGED
        mock_session.diff.return_value = "-old\n+new"
        monkeypatch.setattr("src.gitnotes.cli.Session", lambda *a, **kw: mock_session)

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as _:
            result = runner.invoke(main, ["new", "test-note"], input="y\n")
            assert result.exit_code == 0
            assert Path("test-note.md").is_file()
            mock_session.edit.assert_called_once()
            mock_session.commit.assert_called_once()

    def test_editor_flag_overrides_resolve(self, tmp_path, monkeypatch):
        resolve_called = False
        def track_resolve():
            nonlocal resolve_called
            resolve_called = True
            return "vim"
        monkeypatch.setattr("src.gitnotes.cli.resolve_editor", track_resolve)
        mock_session = MagicMock()
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = None
        mock_session.edit.return_value = EditResult.CHANGED
        mock_session.diff.return_value = ""
        monkeypatch.setattr("src.gitnotes.cli.Session", lambda *a, **kw: mock_session)

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as _:
            result = runner.invoke(main, ["new", "test-note", "--editor", "nano"], input="y\n")
            assert result.exit_code == 0
            assert not resolve_called
            mock_session.edit.assert_called_once_with("nano")

    def test_empty_file_result(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.gitnotes.cli.resolve_editor", lambda: "vim")
        mock_session = MagicMock()
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = None
        mock_session.edit.return_value = EditResult.EMPTY
        monkeypatch.setattr("src.gitnotes.cli.Session", lambda *a, **kw: mock_session)

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as _:
            result = runner.invoke(main, ["new", "test-note"], input="n\n")
            assert result.exit_code == 1
            mock_session.restore.assert_called_once()

    def test_exit_1_on_config_not_resolved(self, tmp_path, monkeypatch):
        def raise_error(*a, **kw):
            raise ConfigNotResolvedError("No editor found")
        monkeypatch.setattr("src.gitnotes.cli.resolve_editor", raise_error)

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as _:
            result = runner.invoke(main, ["new", "test-note"])
            assert result.exit_code == 1

    def test_exit_1_on_lock_contention(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.gitnotes.cli.resolve_editor", lambda: "vim")

        def raise_oserror(*a, **kw):
            raise OSError("Lock file held by another process")
        monkeypatch.setattr("src.gitnotes.cli.Session", raise_oserror)

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as _:
            result = runner.invoke(main, ["new", "test-note"])
            assert result.exit_code == 1


class TestEditCli:
    def test_edit_existing_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.gitnotes.cli.resolve_editor", lambda: "vim")
        mock_session = MagicMock()
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = None
        mock_session.edit.return_value = EditResult.CHANGED
        mock_session.diff.return_value = "-old\n+new"
        monkeypatch.setattr("src.gitnotes.cli.Session", lambda *a, **kw: mock_session)

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as _:
            Path("test-note.md").write_text("existing content\n")
            result = runner.invoke(main, ["edit", "test-note"], input="y\n")
            assert result.exit_code == 0
            mock_session.edit.assert_called_once()
            mock_session.commit.assert_called_once()

    def test_edit_nonexistent_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.gitnotes.cli.resolve_editor", lambda: "vim")
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as _:
            result = runner.invoke(main, ["edit", "nonexistent"])
            assert result.exit_code == 1

    def test_edit_editor_flag_overrides(self, tmp_path, monkeypatch):
        resolve_called = False
        def track_resolve():
            nonlocal resolve_called
            resolve_called = True
            return "vim"
        monkeypatch.setattr("src.gitnotes.cli.resolve_editor", track_resolve)
        mock_session = MagicMock()
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = None
        mock_session.edit.return_value = EditResult.CHANGED
        mock_session.diff.return_value = ""
        monkeypatch.setattr("src.gitnotes.cli.Session", lambda *a, **kw: mock_session)

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as _:
            Path("test-note.md").write_text("existing content\n")
            result = runner.invoke(main, ["edit", "test-note", "--editor", "nano"], input="y\n")
            assert result.exit_code == 0
            assert not resolve_called
            mock_session.edit.assert_called_once_with("nano")

    def test_edit_with_md_extension(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.gitnotes.cli.resolve_editor", lambda: "vim")
        mock_session = MagicMock()
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = None
        mock_session.edit.return_value = EditResult.CHANGED
        mock_session.diff.return_value = ""
        monkeypatch.setattr("src.gitnotes.cli.Session", lambda *a, **kw: mock_session)

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as _:
            Path("test-note.md").write_text("existing content\n")
            result = runner.invoke(main, ["edit", "test-note.md"], input="y\n")
            assert result.exit_code == 0
            mock_session.edit.assert_called_once()


class TestSearchCli:
    def test_search_with_results(self, tmp_path, monkeypatch):
        mock_result = SearchResult(
            matches=(SearchMatch("test.md", 1, "hello world", (), ()),),
            raw="test.md:1:hello world\n",
            exit_code=0,
        )
        monkeypatch.setattr("src.gitnotes.cli.search_notes", lambda q: mock_result)

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as _:
            result = runner.invoke(main, ["search", "hello"])
            assert result.exit_code == 0
            assert "test.md" in result.output

    def test_search_no_results(self, tmp_path, monkeypatch):
        mock_result = SearchResult(matches=(), raw="", exit_code=1)
        monkeypatch.setattr("src.gitnotes.cli.search_notes", lambda q: mock_result)

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as _:
            result = runner.invoke(main, ["search", "hello"])
            assert result.exit_code == 1

    def test_search_context_flag(self, tmp_path, monkeypatch):
        captured = {}
        def track_search(query):
            captured["query"] = query
            return SearchResult(matches=(), raw="", exit_code=1)
        monkeypatch.setattr("src.gitnotes.cli.search_notes", track_search)

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as _:
            runner.invoke(main, ["search", "--context", "5", "hello"])
            assert captured["query"] == "hello"

    def test_search_json_output(self, tmp_path, monkeypatch):
        mock_result = SearchResult(
            matches=(SearchMatch("test.md", 1, "hello world", (), ()),),
            raw="test.md:1:hello world\n",
            exit_code=0,
        )
        monkeypatch.setattr("src.gitnotes.cli.search_notes", lambda q: mock_result)

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as _:
            result = runner.invoke(main, ["search", "--json", "hello"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert len(data) == 1
            assert data[0]["file"] == "test.md"
            assert data[0]["line"] == 1
            assert data[0]["content"] == "hello world"


class TestExportCli:
    def test_export_success(self, tmp_path, monkeypatch):
        mock_result = ExportResult(
            success=True, exit_code=0, stderr="",
            output_path=Path("test-note.html"),
        )
        monkeypatch.setattr("src.gitnotes.cli.export_note", lambda p: mock_result)

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as _:
            Path("test-note.md").write_text("# Hello\n")
            result = runner.invoke(main, ["export", "test-note"])
            assert result.exit_code == 0

    def test_export_failure(self, tmp_path, monkeypatch):
        mock_result = ExportResult(
            success=False, exit_code=1, stderr="pandoc error",
            output_path=Path("test-note.html"),
        )
        monkeypatch.setattr("src.gitnotes.cli.export_note", lambda p: mock_result)

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as _:
            Path("test-note.md").write_text("# Hello\n")
            result = runner.invoke(main, ["export", "test-note"])
            assert result.exit_code == 1

    def test_export_format_flag(self, tmp_path, monkeypatch):
        captured = {}
        def track_export(note_path):
            captured["note_path"] = note_path
            return ExportResult(
                success=True, exit_code=0, stderr="",
                output_path=Path("test-note.pdf"),
            )
        monkeypatch.setattr("src.gitnotes.cli.export_note", track_export)

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as _:
            Path("test-note.md").write_text("# Hello\n")
            result = runner.invoke(main, ["export", "--format", "pdf", "test-note"])
            assert result.exit_code == 0
            assert str(captured["note_path"]).endswith("test-note.md")

    def test_export_pandoc_not_found(self, tmp_path, monkeypatch):
        mock_result = ExportResult(
            success=False, exit_code=None, stderr="pandoc not found",
            output_path=None,
        )
        monkeypatch.setattr("src.gitnotes.cli.export_note", lambda p: mock_result)

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as _:
            Path("test-note.md").write_text("# Hello\n")
            result = runner.invoke(main, ["export", "test-note"])
            assert result.exit_code == 2
