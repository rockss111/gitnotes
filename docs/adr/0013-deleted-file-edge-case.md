# Deleted File Edge Case

## Status
Accepted

## Context
A user might accidentally delete the note file, or a process might delete it during an editing session (crash, script error, etc.). We need to detect and recover gracefully.

We considered several approaches:
- **A**: Hash + error handling (detect via missing file)
- **B**: File existence check only
- **C**: Git status hooks integration

## Decision
**Choice: A (hash + error handling)**

- If file missing post-edit: show snapshot, offer restore
- Clean recovery from crash/state mismatch

### Implementation Details
1. After editor exits, check if file exists:
   ```python
   if not os.path.exists(filepath):
       # File was deleted (crash or manual)
   ```
2. If missing and we have a pre-edit snapshot:
   - Show: "Note file is missing. Restore from last session?"
3. User options:
   - **Restore**: Recreate file from `.gitnotes/sessions/<name>.pre-edit`
   - **Skip**: Leave as-is (file will be recreated on next read)
4. If no snapshot available, show error and suggest re-reading the note

### Why Hash/Existence Check?
- **Accurate**: Detects actual file absence vs. just empty content
- **Non-destructive**: Can always restore from pre-edit snapshot
- **Crash-tolerant**: Works even if deletion happened mid-session
- **Minimal overhead**: Simple existence check, no complex logic

## Consequences

### Positive
- Crash-safe: Clean recovery even if file deleted during session
- Non-destructive: Can always restore from pre-edit snapshot
- Transparent to user: Clear prompts explain what happened
- Minimal overhead: One existence check after editor exits

### Negative
- Slight friction: User must respond before commit completes
- Could be confused if user doesn't understand why prompted

### Future Implications
- Can track "deletion history" for audit purposes
- Snapshot restore works with any content, not just non-empty files