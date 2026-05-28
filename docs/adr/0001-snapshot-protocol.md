# Session Snapshot Protocol (Hash-Based, Crash-Safe)

## Status
Accepted

## Context
During an editing session, we need to detect what changed in the note file. The challenge is doing this reliably even if the editor crashes or the user manually edits the file between sessions.

We considered several approaches:
- **A**: Hash-based comparison with snapshot files (store pre-edit hash and full content)
- **B**: Delta-based diff tracking (track line-by-line changes)
- **C**: Event-based logging (log all editor events)

## Decision
**Choice: A (hash-based, snapshot file)**

- Hash: SHA256 of `file.md` before/after edit
- Snapshot: `.gitnotes/sessions/<name>.pre-edit` stores the full pre-edit content for crash recovery

### Implementation Details
1. On session start, compute SHA256 hash of current file content
2. Write full file contents to `.gitnotes/sessions/<name>.pre-edit`
3. After editor exits, recompute hash and compare
4. If hashes differ, show unified diff for user review
5. Store both pre- and post-edit hashes in session metadata

### Why Hash-Based?
- **Deterministic**: Same content always produces same hash
- **Fast**: SHA256 is extremely fast on modern CPUs (~10MB/s+)
- **Simple**: No need to parse markdown or YAML for change detection
- **Crash-safe**: Full snapshot allows recovery even if file is deleted

## Consequences

### Positive
- Crash recovery: If process dies, full pre-edit content can be restored
- Precise "what changed" signal: User sees exactly what they modified
- Minimal overhead: Hash computation adds <1ms to session start

### Negative
- Snapshot files grow with file size (but only one active at a time)
- Slight disk I/O for reading/writing snapshot before each edit

### Future Implications
- Can extend to track multiple pre-edit states if needed
- Hash-based approach works for any text format, not just markdown