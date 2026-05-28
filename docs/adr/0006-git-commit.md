# Git Commit

## Status
Accepted

## Context
After an editing session, we need to commit the changes back to Git. The commit should be atomic and have a meaningful message that indicates what happened.

We considered several approaches:
- **A**: Single file, meaningful message (`git add <file> + git commit -m "<action>: <title>"`)
- **B**: Batch multiple related files in one commit
- **C**: Use Git hooks to auto-commit on exit

## Decision
**Choice: C (single file, meaningful message)**

- `git add <file>` + `git commit -m "<action>: <title>"`
- Only if hash indicates change

### Implementation Details
1. After successful edit and user review, run:
   ```bash
   git add notes/<filename>.md
   git commit -m "edit: <note title>"
   ```
2. Use the note's YAML front matter `title` field for the message
3. Only commit if hash comparison shows actual changes occurred
4. Skip commit if file is unchanged (no diff)

### Why This Approach?
- **Clean**: One atomic operation per edit session
- **Atomic**: Either all or nothing; no partial commits
- **Meaningful history**: Commit messages show what action was taken and which note was modified
- **Per-action granularity**: Each edit gets its own commit, making review easier

## Consequences

### Positive
- Clean, atomic commits: Easy to review what changed in each session
- Meaningful history: `git log` shows "edit: Note Title" pattern
- Minimal Git overhead: Single file operations are fast

### Negative
- More commits than other approaches (one per edit session)
- Could be seen as noisy if user edits same note frequently

### Future Implications
- Can batch multiple edits in one commit if needed later
- Per-action granularity enables fine-grained review of individual sessions