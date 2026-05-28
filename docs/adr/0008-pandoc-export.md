# Pandoc Export

## Status
Accepted

## Context
GitNotes can export a note's markdown content as HTML using Pandoc, leveraging YAML front matter embedded in the file for metadata.

We considered several approaches:
- **A**: Simple invocation + pre-flight check (check pandoc exists before running)
- **B**: Full CLI with custom options (`pandoc --metadata ...`)
- **C**: In-memory conversion without file I/O

## Decision
**Choice: A (simple invocation) + B (pre-flight check)**

- `pandoc file.md -o file.html`
- Pre-check: `shutil.which("pandoc")` or `exec.LookPath`
- Post-check: Exit code + stderr; retry on failure

### Implementation Details
1. **Pre-flight**: Check if pandoc is in PATH before attempting export
2. **Invoke**: Simple command-line invocation:
   ```bash
   pandoc notes/<filename>.md -o <filename>.html
   ```
3. **Post-check**: Verify exit code (0 = success) and check stderr for errors
4. **Retry logic**: If first attempt fails, retry once with increased timeout; then show detailed error

### Why Simple + Pre-flight?
- **Leverages YAML front matter**: Pandoc automatically reads title, date, tags from front matter
- **Minimal overhead**: No custom parsing or CLI options needed for basic export
- **Pre-flight check**: Prevents cryptic errors if pandoc not installed
- **Retry on failure**: Handles transient issues (network, temp files)

## Consequences

### Positive
- Leverages embedded YAML front matter automatically
- Minimal overhead: Simple command-line invocation
- Robust error handling with retry logic
- Works with any Pandoc-compatible front matter format

### Negative
- Custom metadata extraction requires parsing HTML output (not a blocker for basic use)
- Limited to files where pandoc can read embedded YAML

### Future Implications
- Can add custom CLI options if more control needed later
- Pre-flight check pattern can be reused for other external tools