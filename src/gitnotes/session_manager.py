"""
Session Locking

Per ADR-0002:
- Lock file: .gitnotes/sessions/<name>.lock
- Auto-released on process exit (clean or crash)
- Uses fcntl.flock for cross-platform advisory locking
"""

import os
import fcntl
from pathlib import Path

# Track lock file descriptors for release by name
_locks: dict[str, int] = {}


def acquire_lock(name: str) -> int:
    """
    Acquire an exclusive advisory lock on a session file.

    Args:
        name: Session identifier (e.g., note filename)

    Returns:
        int: File descriptor for the lock (pass to release_lock)

    Raises:
        BlockingIOError: If lock is already held by another session
        OSError: If the lock cannot be acquired

    Lock file path: .gitnotes/sessions/<name>.lock
    """
    repo_path = Path.cwd()
    sessions_dir = repo_path / ".gitnotes" / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)

    lock_path = sessions_dir / f"{name}.lock"
    fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        os.close(fd)
        raise

    _locks[name] = fd
    return fd


def release_lock(name: str) -> None:
    """
    Release a session lock by closing its file descriptor.

    Args:
        name: Session identifier (e.g., note filename)
    """
    fd = _locks.pop(name, None)
    if fd is not None:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        except OSError:
            pass
        os.close(fd)

    lock_path = Path.cwd() / ".gitnotes" / "sessions" / f"{name}.lock"
    if lock_path.exists():
        try:
            lock_path.unlink()
        except OSError:
            pass
