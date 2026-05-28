# External Change Recovery

## Status
Accepted

## Context
A user might manually edit a note file using VS Code, nano, or another editor before or during the GitNotes editing session. We need to detect and handle these "external changes" gracefully.

We considered several approaches:
- **A**: Hash pre/post-snapshot comparison (detect via hash mismatch)
- **B**: File modification time tracking
- **C**: Git status hooks integration

## Decision
**Choice: A (hash pre/post-snapshot)**

- Pre-editor check: Hash file vs. snapshot; if different, warn user
- Post-editor check: Compare again after editor exits
- User choice: Accept diff, retry edit, or revert

### Implementation Details
1. **Before spawning editor**: Check if current hash differs from pre-edit snapshot (indicates external change)
2. If different, show warning and offer options:
   - Continue with current content
   - Restore from last known good state
3. **After editor exits**: Compare again to catch any more changes
4. Present unified diff for user review regardless of source
5. User can: Accept (commit changes), Retry (spawn editor again), or Revert (restore snapshot)

### Why Hash-Based?
- **Accurate**: Detects actual content changes, not just file access time
- **Non-blocking**: Fast comparison (<1ms for typical files)
- **Transparent to user**: Works regardless of how changes occurred
- **Minimal overhead**: Only one hash check before and after edit

## Consequences

### Positive
- Transparent to user: No silent corruption or data loss
- Flexible recovery options: Accept, retry, or revert based on user choice
- Works with any text editor (black-box model)

### Negative
- Slightly more complex flow: Need to handle 3+ states (unmodified, modified before edit, modified after edit)
- User might be confused by multiple prompts in unusual scenarios

### Future Implications
- Can track "edit history" of a note across sessions
- Could implement auto-retry if external changes detected repeatedly