"""
Editing session lifecycle.

Single deep module replacing session_manager.py, snapshot.py, editor.py.

- ADR-0001 (Snapshot protocol): SHA256 hash + pre-edit snapshot
- ADR-0002 (Session locking): flock-based advisory locking
- ADR-0003 (Post-editor validation): exists, non-empty, UTF-8
- ADR-0004 (Change detection): unified diff via Python difflib
- ADR-0006 (Git commit): git add + git commit with meaningful message
"""

import difflib
import enum
import fcntl
import hashlib
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SessionPaths:
    dir: Path
    lock: Path
    snapshot: Path

    @classmethod
    def for_note(cls, repo_path: Path, name: str) -> "SessionPaths":
        d = cls.base_dir(repo_path)
        return cls(
            dir=d,
            lock=d / f"{name}.lock",
            snapshot=d / f"{name}.pre-edit",
        )

    @staticmethod
    def base_dir(repo_path: Path) -> Path:
        return repo_path / ".gitnotes" / "sessions"


class EditResult(enum.Enum):
    UNCHANGED = 0
    CHANGED = 1
    EMPTY = 2
    DELETED = 3
    INVALID = 4


class Session:
    def __init__(self, name: str, repo_path: Path | None = None):
        self._name = name
        self._repo_path = repo_path or Path.cwd()
        self._note_path = self._repo_path / name
        self._paths = SessionPaths.for_note(self._repo_path, name)
        self._lock_fd: int | None = None
        self._pre_edit_hash: str | None = None

        self._acquire_lock()
        self._create_snapshot()

    # ---- Public interface ----

    def check_external_change(self) -> bool:
        return self._hash_file(self._note_path) != self._pre_edit_hash

    def edit(self, editor_cmd: str) -> EditResult:
        self._spawn_editor(editor_cmd)

        if not self._note_path.exists():
            return EditResult.DELETED

        if self._note_path.stat().st_size == 0:
            return EditResult.EMPTY

        if not self._validate():
            return EditResult.INVALID

        if not self._has_changed():
            return EditResult.UNCHANGED

        return EditResult.CHANGED

    def diff(self) -> str:
        if not self._paths.snapshot.exists():
            return ""

        before = self._paths.snapshot.read_text(encoding="utf-8")
        after = self._note_path.read_text(encoding="utf-8")

        if before == after:
            return ""

        diff = difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"a/{self._name}",
            tofile=f"b/{self._name}",
        )
        return "".join(diff)

    def commit(self) -> bool:
        if not self._has_changed():
            return False

        subprocess.run(
            ["git", "add", str(self._note_path)],
            check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", f"edit: {self._name}"],
            check=True, capture_output=True,
        )
        return True

    def restore(self) -> None:
        if self._paths.snapshot.exists():
            self._note_path.write_bytes(self._paths.snapshot.read_bytes())

    def close(self) -> None:
        self._release_lock()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    # ---- Private helpers ----

    def _acquire_lock(self) -> None:
        self._paths.dir.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(self._paths.lock), os.O_CREAT | os.O_RDWR)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            os.close(fd)
            raise
        self._lock_fd = fd

    def _release_lock(self) -> None:
        if self._lock_fd is not None:
            try:
                fcntl.flock(self._lock_fd, fcntl.LOCK_UN)
            except OSError:
                pass
            os.close(self._lock_fd)
            self._lock_fd = None

        if self._paths.lock.exists():
            try:
                self._paths.lock.unlink()
            except OSError:
                pass

    def _create_snapshot(self) -> None:
        content = self._note_path.read_bytes()
        self._paths.dir.mkdir(parents=True, exist_ok=True)
        self._paths.snapshot.write_bytes(content)
        self._pre_edit_hash = hashlib.sha256(content).hexdigest()

    def _has_changed(self) -> bool:
        if not self._paths.snapshot.exists():
            return True
        return self._hash_file(self._note_path) != self._pre_edit_hash

    def _spawn_editor(self, editor_cmd: str) -> int:
        result = subprocess.run(
            [editor_cmd, str(self._note_path)],
            check=False,
        )
        return result.returncode

    def _validate(self) -> bool:
        if not self._note_path.exists():
            return False
        if self._note_path.stat().st_size == 0:
            return False
        try:
            with open(self._note_path, "rb") as f:
                chunk = f.read(4096)
            chunk.decode("utf-8")
            return True
        except (UnicodeDecodeError, OSError):
            return False

    @staticmethod
    def _hash_file(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()
