# Search (git grep with context)

## Status
Accepted

## Context
GitNotes needs a fast, content-focused search tool that can find matches across all tracked markdown files.

We considered several approaches:
- **A**: `git grep` with context and exclusions
- **B**: Full-text index (like SQLite FTS)
- **C**: Regex-based in-memory search

## Decision
**Choice: C (git grep with context)**

- `git grep -i -n -C 3 --heading --break -e "<query>"`
- Exclude `.git/`, `.gitnotes/` from results

### Implementation Details
1. Use `git grep` to search across all tracked files in the repository
2. Flags used:
   - `-i`: Case-insensitive matching (user-friendly)
   - `-n`: Show line numbers for precise location
   - `-C 3`: Show 3 lines of context before/after match
   - `--heading`: Show file heading with each result
   - `--break`: Break long output into pages
3. Automatically exclude internal directories (`.git/`, `.gitnotes/`)

### Why git grep?
- **Fast**: Uses Git's optimized search algorithms
- **Content-focused**: Searches actual file contents, not filenames or metadata
- **Readable**: Context makes it easy to understand matches
- **Tracked files only**: Automatically respects `.gitignore`, `.gitattributes`

## Consequences

### Positive
- Fast: Leverages Git's optimized search (much faster than naive grep)
- Content-focused: Searches actual note contents, not filenames/metadata
- Readable: Context and headings make results easy to scan
- Automatic exclusions: Respects `.gitignore` automatically

### Negative
- Only searches tracked files (not untracked or deleted notes)
- Regex-based matching might miss some edge cases in complex queries

### Future Implications
- Can add full-text indexing if search performance becomes a bottleneck
- `--heading` flag provides good balance between detail and readability