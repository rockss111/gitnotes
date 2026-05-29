# CLI Architecture & CLI–Session Boundary

## Status
Accepted

## Context
A CLI layer is needed to expose the core GitNotes library functions (`init_repository`, `resolve_editor`, `Session`, `search_notes`, `export_note`) as user-facing commands. The CLI must handle all user interaction (prompts, output formatting, exit codes) while the library modules remain pure, testable state machines.

We considered:
- **A**: Embedding user interaction inside `Session` methods
- **B**: Separating CLI concerns into a distinct `cli.py` with `Session` as a pure API

## Decision
**Option B: CLI owns all user interaction; `Session` is a pure state machine.**

```
┌──────────────────────┐     ┌──────────────────────┐
│        CLI           │     │       Session         │
│  (cli.py)            │────▶│  (session.py)         │
│                      │     │                      │
│  • editor resolution │     │  • lock acquire       │
│  • user prompts      │     │  • snapshot create    │
│  • diff display      │     │  • editor spawn       │
│  • accept/reject     │     │  • post-edit validate │
│  • exit codes        │     │  • diff computation   │
│                      │     │  • git commit         │
└──────────────────────┘     └──────────────────────┘
```

### Command Structure

Five commands, each delegating to a library function or the `_edit_session` helper:

| Command | Library Delegate | Key Behaviour |
|---------|-----------------|---------------|
| `init` | `init_repository()` | Bootstrap git + `.gitnotes/` dirs |
| `new <name>` | `_edit_session()` | Create file, then session lifecycle |
| `edit <name>` | `_edit_session()` | File must exist, then session lifecycle |
| `search <query>` | `search_notes()` | Human or JSON output |
| `export <name>` | `export_note()` | Pandoc export with format flag |

### Exit Codes

| Code | Meaning | Scenarios |
|------|---------|-----------|
| 0 | Success | All happy paths |
| 1 | User/domain error | `ConfigNotResolvedError`, `InitializationError`, file not found, lock contention, no matches, empty/invalid after retry, pandoc failure |
| 2 | System error | Git not found, pandoc not found, pandoc timeout |

### `_edit_session` Shared Helper

Both `new` and `edit` share identical session lifecycle logic (editor resolution, lock acquisition, editor spawn, result handling, commit/restore). This is extracted into a private `_edit_session(name, editor)` helper in `cli.py`:

1. Resolve editor via config cascade, or use `--editor` override
2. Open `Session(name)` as context manager (acquires lock, takes snapshot)
3. Call `session.edit(editor_cmd)` → `EditResult`
4. Handle each result:
   - `CHANGED`: show diff, prompt accept/reject, commit or restore
   - `EMPTY`: prompt keep/restore, restore exits 1
   - `DELETED`: inform user, restore, exit 1
   - `INVALID`: inform user, restore, exit 1
   - `UNCHANGED`: no-op (exit 0)

The caller (`new` or `edit`) handles only file-level concerns before delegating.

### ADR Cross-References

- **ADR-0007 (Config Cascade)**: CLI calls `resolve_editor()` from `config_resolver.py`, with `--editor` flag as an override that bypasses the cascade entirely.
- **ADR-0008 (Pandoc Export)**: CLI accepts `--format` flag (default `"html"`) and passes the note path to `export_note()`. When the result indicates pandoc is not found (`exit_code is None`), CLI exits 2.
- **ADR-0009 (Search Command)**: CLI accepts `--context` (default 3) and `--json` flag. Human-readable output prints raw `git grep` output; `--json` serialises `SearchMatch` objects as structured JSON.
- **ADR-0011 (Initialization)**: `init` command delegates directly to `init_repository()`, catching `InitializationError` for exit 1 and pre-checking for git binary for exit 2.
- **ADR-0014 (Testability)**: CLI tests use `click.testing.CliRunner` with monkeypatched library functions, following the hybrid unit/integration approach.

## Consequences

### Positive
- `Session` remains testable without user interaction concerns
- CLI logic is isolated for focused testing
- Exit code policy is enforced in one layer
- `new` and `edit` share the session lifecycle without duplication

### Negative
- CLI introduces an additional abstraction layer
- Some error states must be detected at the CLI level (e.g., missing git binary)

### Future Implications
- Adding new commands follows the same pattern (thin wrapper → library delegate)
- The `_edit_session` helper can be extended for retry logic without touching the commands
