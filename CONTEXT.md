# GitNotes Domain Context

## Glossary

### note
A markdown file tracked in the Git repository. Each note is a versioned document that can contain YAML front matter for tags and metadata.

### snapshot
A pre-edit copy of a note file stored in `.gitnotes/sessions/<name>.pre-edit`. This provides crash-safe, deterministic change detection by comparing SHA256 hashes of the original and post-edit states.

### session lock
An exclusive advisory lock (via `flock`) on `.gitnotes/sessions/<name>.lock` that ensures only one editing session can modify a specific note file at a time.

### pre-edit hash
The SHA256 hash of the note file content computed immediately before spawning the external editor. Used to detect whether (and how) the file changed during the editing session.

### external editor
A user-configured text editor (e.g., `vim`, `nano`) spawned as a child process. GitNotes treats the editor as a black box, spawning it and waiting for exit without interpreting its behavior.

### config cascade
A three-tier configuration system:
1. Project-level `.gitnotes` file (committed to the repo)
2. User global `~/.config/gitnotes/config` (uncommitted, persistent preferences)
3. Environment variables (e.g., `GITNOTES_EDITOR`) as emergency overrides

### pandoc export
Conversion of a markdown note into HTML using `pandoc file.md -o file.html`. Relies on YAML front matter embedded in the markdown for metadata.

### git grep search
Content-based search using `git grep -i -n -C 3 --heading --break` to find matches across all tracked markdown files, excluding internal directories.

### init protocol
The explicit `gitnotes init` command that bootstraps a new GitNotes repository by initializing Git, creating `.gitnotes/`, adding `.gitattributes`, and committing with "Initialized GitNotes".

### external change
Modifications to a note file made by another process (e.g., VS Code, manual edit) before or during the GitNotes editing session. Detected via hash comparison and resolved with user choice.

---

## Architecture Overview

GitNotes is a versioned note-taking CLI that treats each markdown file as a Git-tracked "note". The core loop is:

1. **Init**: User runs `gitnotes init` to create `.git/`, `.gitnotes/`, `.gitattributes`, and an initial commit.
2. **Create/Edit**: User runs `note new` or `note edit`, which:
   - Acquires a session lock via `flock`.
   - Saves a pre-edit snapshot (for crash safety).
   - Spawns the configured external editor.
   - Waits for exit, computes post-edit hash, compares to snapshot.
   - Shows diff if changed; user accepts/rejects/retries.
   - Commits the file with a meaningful commit message.
3. **Search**: `note search` uses `git grep` with context and exclusions.
4. **Export**: `note export` runs Pandoc on the file; pre-flight and retry checks handle errors.

All file I/O is minimal and focused on preserving user intent, with robust recovery from crashes, external edits, or empty files.
