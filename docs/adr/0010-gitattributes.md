# .gitattributes

## Status
Accepted

## Context
GitNotes needs to ensure consistent line ending behavior across different operating systems (Windows, macOS, Linux) for predictable diffs and portable files.

We considered several approaches:
- **A**: `*.md text eol=lf` (auto-create on gitnotes init)
- **B**: Per-file attributes in `.gitattributes`
- **C**: Git hooks to normalize line endings

## Decision
**Choice: A (*.md text eol=lf)**

- Auto-create on `gitnotes init`
- Ensures LF line endings across platforms

### Implementation Details
1. On `gitnotes init`, write `.gitattributes` with:
   ```text
   *.md text eol=lf
   ```
2. This tells Git to treat all markdown files as text and use LF (Unix-style) line endings
3. Automatically applies when committing/pushing, normalizing across platforms

### Why This?
- **Portable**: LF is the universal standard for cross-platform consistency
- **Predictable diffs**: No `CRLF` vs `LF` confusion in version control
- **Auto-create**: Minimal setup; just works on project initialization
- **Minimal overhead**: Single line, applies to all markdown files automatically

## Consequences

### Positive
- Portable: LF is the universal standard for cross-platform consistency
- Predictable diffs: No `CRLF` vs `LF` confusion in version control
- Auto-create: Minimal setup; just works on project initialization
- Minimal overhead: Single line, applies to all markdown files automatically

### Negative
- Slight Git overhead (normalizing CRLF→LF on Windows)
- Users might expect their native line endings to be preserved

### Future Implications
- Can extend to other file types if needed (e.g., `.yml` for front matter files)
- Pattern `*.md` is broad enough to cover most use cases