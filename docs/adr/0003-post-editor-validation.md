# Post-Editor Validation

## Status
Accepted

## Context
After an external editor exits, we need to verify that the file is in a good state before committing changes back to Git.

We considered several approaches:
- **A**: Existence + size check only (fast, minimal)
- **B**: Existence + non-empty + UTF-8 validation
- **C**: Full semantic validation (YAML front matter, Markdown syntax)

## Decision
**Choice: B + UTF-8 check**

- File must exist, be non-empty, and valid UTF-8
- Semantic (YAML/Markdown) validation deferred to read-time

### Implementation Details
1. Check file exists and size > 0
2. Read first 4KB and verify UTF-8 validity
3. If UTF-8 invalid, show error and offer restore from snapshot
4. Semantic validation happens when user next reads the note (not on save)

### Why This Balance?
- **Fast**: Size check is O(1), UTF-8 check only reads 4KB max
- **Non-blocking**: No need to parse entire file or validate complex syntax
- **Minimal friction**: Users can write raw text without worrying about Markdown rules
- **Deferred semantic validation**: Keep edit flow simple; catch errors when reading, not saving

## Consequences

### Positive
- Fast validation: <1ms for typical note files
- Non-blocking save: User doesn't wait for complex parsing
- Minimal friction: Write anything valid UTF-8 without rules

### Negative
- Semantic errors (invalid YAML front matter) won't catch until read-time
- Could commit malformed Markdown (acceptable; Git handles it)

### Future Implications
- Can add stricter validation later if needed
- 4KB buffer could increase for very large files