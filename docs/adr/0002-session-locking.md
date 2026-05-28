# Session Locking (flock)

## Status
Accepted

## Context
When a user starts editing a note, we need to ensure only one session can modify that specific file at a time. This prevents race conditions where two users might think they're editing the same note simultaneously.

We considered several approaches:
- **A**: Advisory lock files with `flock` (Unix) or `LockFile` module (cross-platform)
- **B**: In-memory lock tracking via Git hooks
- **C**: File-based locking using `.git/refs/notes/<name>.locked`

## Decision
**Choice: A (flock)**

- Lock file: `.gitnotes/sessions/<name>.lock`
- Auto-released on process exit (clean or crash)

### Implementation Details
1. Use `flock -x` for exclusive locking when spawning the editor
2. Lock is automatically released when the parent process exits
3. Lock files are stored in `.gitnotes/sessions/` alongside snapshots
4. On startup, check if lock exists and warn user if stale

### Why flock?
- **Simple**: Built into most Unix shells, no external dependencies
- **Cross-process**: Works even if another process holds the lock
- **Auto-release**: Even crashes release locks automatically
- **Lightweight**: Minimal filesystem overhead (single file per session)

## Consequences

### Positive
- Prevents accidental concurrent edits on same note
- Simple, well-understood mechanism
- Crash-tolerant: locks released even if process dies

### Negative
- Advisory lock: another user could manually edit the file anyway (acceptable given black-box model)
- Lock files add minimal disk usage (~1KB per active session)

### Future Implications
- Can extend to track lock duration for debugging
- Could implement lock timeout/recovery logic if needed