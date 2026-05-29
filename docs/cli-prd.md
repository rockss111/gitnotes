# CLI Interface for GitNotes

## Status

Draft

## Goal

Add a `click`-based CLI to GitNotes for the four user-facing commands: `init`, `new`, `edit`, `search`, `export`.

## Commands

### `gitnotes init`

Bootstrap a GitNotes repository. Delegates to `init_repository()`. No flags.

- Exit 0 on success
- Exit 1 on `InitializationError` (e.g., missing `git user.name`)
- Exit 2 on system errors (e.g., git binary not found)

### `gitnotes new <name>`

Create a new note and open it in the external editor.

- Auto-append `.md` if `name` has no file extension
- Create an empty file at `name.md`
- Construct `Session(name)` (acquires lock, takes snapshot)
- Resolve editor via `resolve_editor()` — or use `--editor` if provided
- Call `session.edit(editor_cmd)`
- Prompt on `EMPTY`, `DELETED`, `INVALID` (retry / restore)
- Show diff on `CHANGED`, prompt accept/reject
- Call `session.commit()` if accepted
- Exit 1 on lock contention, `ConfigNotResolvedError`, empty/invalid after retry
- Exit 0 on success

Flags:

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--editor` | `str` | — | Override editor for this session (bypasses config cascade) |

### `gitnotes edit <name>`

Open an existing note for editing.

- Same lifecycle as `new`, except the file must already exist
- Error with exit 1 if `name.md` does not exist

Flags: same as `new`.

### `gitnotes search <query>`

Search note contents via `git grep`. Delegates to `search_notes()`.

- Default output: human-readable lines (file:line:content with context)
- `--json`: emit structured JSON with all matches, file, line, context
- Pass `--context` to `search_notes()` as context line count

Flags:

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--context` | `int` | 3 | Lines of context before/after each match |
| `--json` | `bool` | False | Output structured JSON instead of human-readable |

- Exit 0 on matches found
- Exit 1 on no matches
- Exit 2 on git command failure

### `gitnotes export <name> <output_format>`

Export a note via pandoc. Delegates to `export_note()`.

- `--format`: arbitrary pandoc output format string
- CLI maps known format names to file extensions (html→.html, pdf→.pdf, docx→.docx, etc.), falls back to `.out` for unknown formats
- Pass format through to `export_note()` as `output_format` parameter

Flags:

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--format` | `str` | `"html"` | Pandoc output format |

- Exit 0 on success
- Exit 1 on file not found
- Exit 2 on pandoc not found or pandoc failure

## CLI–Session Boundary

The CLI owns **all user interaction**. The `Session` class remains a pure state machine:

| Responsibility | Owner |
|---|---|
| Editor resolution | CLI (calls `resolve_editor()`) |
| Lock acquisition | `Session.__init__` |
| Snapshot creation | `Session.__init__` |
| Editor spawning | `Session.edit()` |
| Post-edit validation | `Session.edit()` returns `EditResult` |
| Diff computation | `Session.diff()` returns `str` |
| Diff display | CLI |
| Accept/reject/retry prompts | CLI |
| External change detection | `Session.check_external_change()` |
| External change prompts | CLI |
| Git commit | `Session.commit()` |
| Lock release | `Session.close()` (context manager) |

## Exit Codes

| Code | Meaning | Scenarios |
|------|---------|-----------|
| 0 | Success | All happy paths |
| 1 | User/domain error | `ConfigNotResolvedError`, `InitializationError`, file not found, lock contention, no matches, empty/invalid after retry |
| 2 | System error | Pandoc not found, pandoc timeout, git failure |

## Output Format

All commands produce human-readable text by default. Only `search` supports `--json` for machine-readable output.

## Packaging

- `pyproject.toml` with `click >= 8.0` dependency
- `console_scripts` entry point: `gitnotes = gitnotes.cli:main`
- `__main__.py` for `python -m gitnotes`
- Single CLI module: `src/gitnotes/cli.py`

## ADR Updates

- Update ADR-0008 (pandoc export) — add `--format` flag
- Update ADR-0009 (search command) — add `--context`, `--json` flags
- New ADR-0015 (CLI Architecture) — document CLI–Session boundary

## Non-Goals

- No `--heading` flag on search (always on per ADR-0009)
- No `--max-count` on search (YAGNI)
- No rich terminal UI (plain text + prompts)
- No tab completion (future concern)
- No `delete` command
- No `list` command
