# Empty File Edge Case

## Status
Accepted

## Context
A user might save their note file as completely empty (or accidentally delete all content). We need to handle this gracefully without losing data or confusing the user.

We considered several approaches:
- **A**: Size check + user prompt
- **B**: Treat as valid with warning only
- **C**: Auto-restore from snapshot before committing

## Decision
**Choice: A (size check + user prompt)**

- If size == 0 after editor: ask "Keep empty or restore?"
- Committed if user accepts

### Implementation Details
1. After editor exits, check file size
2. If `os.path.getsize() == 0`:
   - Show message: "Note is now empty. Keep empty or restore from snapshot?"
3. User options:
   - **Keep**: Commit the empty file as-is
   - **Restore**: Revert to pre-edit content from `.gitnotes/sessions/<name>.pre-edit`
4. Store user choice in session metadata for debugging

### Why Explicit Prompt?
- **Explicit, non-destructive**: User makes conscious decision about empty state
- **Snapshot available**: Can always restore if they changed their mind
- **Valid use case**: Empty notes are legitimate (placeholder, TODO items)
- **Minimal overhead**: Simple size check + one prompt

## Consequences

### Positive
- Explicit: User consciously decides what to do with empty content
- Non-destructive: Can always restore from snapshot if needed
- Valid use case: Empty notes serve as placeholders or TODOs
- Minimal overhead: Simple size check + one user prompt

### Negative
- Slight friction: User must respond before commit completes
- Could be confused if user doesn't understand why prompted

### Future Implications
- Can add "auto-keep" option for users who frequently use empty notes
- Snapshot restore works with any content, not just non-empty files