# Initialization

## Status
Accepted

## Context
GitNotes needs an explicit initialization command that bootstraps a new GitNotes repository by initializing Git, creating necessary directories, and setting up configuration.

We considered several approaches:
- **A**: `gitnotes init` command (explicit setup)
- **B**: Auto-initialize on first use of any command
- **C**: Silent initialization with minimal user interaction

## Decision
**Choice: A (gitnotes init command)**

- `git init`, create `.gitnotes/`, write config, add `.gitattributes`
- Initial commit: "Initialized GitNotes"

### Implementation Details
1. Run `git init` if not already initialized
2. Create `.gitnotes/` directory with subdirectories:
   - `.gitnotes/config` (user preferences)
   - `.gitnotes/sessions/` (pre-edit snapshots & locks)
3. Write initial config file to `.gitnotes/config`
4. Add `.gitattributes` with `*.md text eol=lf`
5. Commit everything with message: "Initialized GitNotes"

### Why Explicit?
- **Clean repo state**: User knows when GitNotes is properly set up
- **Explicit setup**: No surprises from auto-initialization behavior
- **Portable**: Works the same regardless of existing Git state
- **Minimal overhead**: One-time operation, then transparent

## Consequences

### Positive
- Clean repo state: User knows exactly when GitNotes is initialized
- Explicit setup: No surprises from auto-behavior
- Portable: Works the same regardless of existing Git state
- Minimal overhead: One-time operation, then transparent

### Negative
- Requires user to remember to run `gitnotes init` before first use
- Slight friction for users who expect "just works" behavior

### Future Implications
- Can add auto-detection if initialization is forgotten (graceful fallback)
- One-time setup keeps subsequent operations fast