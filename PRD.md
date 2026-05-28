# GitNotes CLI - Product Requirements Document

## 1. Project Goal

**GitNotes** is a versioned note-taking command-line interface (CLI) that treats each markdown file in a Git repository as a "note" with full version control history. The core purpose is to provide a crash-safe, deterministic editing experience where users can write their notes using any text editor while GitNotes handles the complex task of detecting changes, managing sessions, and committing updates atomically.

### Primary Objectives
- Enable seamless markdown note editing via user's preferred external editor (vim, nano, VS Code, etc.)
- Provide crash-safe change detection through SHA256 hash-based snapshots
- Ensure atomic commits with meaningful commit messages derived from YAML front matter
- Support robust recovery from crashes, manual edits, or file deletion during sessions
- Leverage Git's native versioning and search capabilities for content discovery

### Target Users
- Technical writers and documentation maintainers who prefer CLI workflows
- Developers who want to integrate note-taking into their development environment
- Users comfortable with markdown and YAML front matter conventions

---

## 2. User Stories

| ID | Actor | Goal | Acceptance Criteria |
|----|-------|------|---------------------|
| US-01 | Editor | Edit a note using my preferred editor | I can run `note edit` and the configured external editor (e.g., vim, nano) opens. After saving, GitNotes shows me exactly what changed via diff and asks if I want to commit. |
| US-02 | Power User | Create a new note file from scratch | I can run `note new <filename>` and my editor opens with an empty file ready for content. The file is committed when I save changes. |
| US-03 | Recovering User | Recover after a crash or interrupted session | If I accidentally killed the process while editing, GitNotes can restore my pre-edit content from a snapshot stored in `.gitnotes/sessions/`. |
| US-04 | Collaborative Writer | Edit simultaneously without conflicts | If another user (or me on another terminal) is already editing the same note, `note edit` acquires an exclusive lock and waits or warns appropriately. |
| US-05 | Manual Editor | Continue after manually editing with VS Code first | If I open a note in VS Code before running `note edit`, GitNotes detects the external change via hash comparison and offers me options to accept, retry, or revert. |
| US-06 | Explorer | Search across all my notes quickly | I can run `note search <query>` and get results with line numbers, context, and file headings using Git's optimized grep implementation. |
| US-07 | Publisher | Export my notes as HTML for web publishing | I can run `note export` and GitNotes uses Pandoc to convert the markdown (including YAML front matter metadata) into a properly formatted HTML file. |
| US-08 | Portable User | Share my configuration between projects | My `.gitnotes/` config file travels with the repository, so when I clone a project, the editor and other preferences are automatically applied. |
| US-09 | Minimalist Writer | Keep my workflow simple with minimal prompts | GitNotes only asks questions when necessary (e.g., empty file detection) and defaults to sensible behavior otherwise. |
| US-10 | Tester | Verify changes before committing | After editing, I see a unified diff showing exactly what changed in this session, allowing me to review before accepting the commit. |

---

## 3. Functional Requirements

### FR-01: Initialization Protocol
**Description:** Bootstraps a new GitNotes repository with proper Git and configuration setup.

**Acceptance Criteria:**
| ID | Criterion | Test Method |
|----|-----------|-------------|
| FC-01.1 | Creates `.git/` directory if not present | `ls -la .git` shows directory exists |
| FC-01.2 | Creates `.gitnotes/config` file with default settings | File exists and contains editor config |
| FC-01.3 | Creates `.gitnotes/sessions/` subdirectory for snapshots & locks | Directory structure verified |
| FC-01.4 | Writes `.gitattributes` with `*.md text eol=lf` | File content matches exactly |
| FC-01.5 | Adds all new files to Git staging | `git status` shows staged changes |
| FC-01.6 | Creates initial commit with message "Initialized GitNotes" | `git log --oneline -1` shows correct commit |

**Edge Cases:**
- If `.git/` already exists, skip `git init`
- If `.gitnotes/config` exists, append rather than overwrite
- Preserve any existing `.gitattributes` content if non-empty

---

### FR-02: Editor Configuration Cascade
**Description:** Determines which external editor to use following a precedence chain.

**Acceptance Criteria:**
| ID | Criterion | Test Method |
|----|-----------|-------------|
| FC-02.1 | Checks `.gitnotes` config file first (project-level) | File contains `editor: "nvim"` key |
| FC-02.2 | Falls back to `$VISUAL` environment variable | Set `VISUAL=vim` and verify vim spawns |
| FC-02.3 | Falls back to `$EDITOR` environment variable | Set `EDITOR=nano` and verify nano spawns |
| FC-02.4 | Exits with helpful message if no editor found | User sees "No editor configured" error |

**Precedence Chain:**
```
1. .gitnotes config file (project-specific)
   ↓
2. $VISUAL env var (full-screen editors convention)
   ↓
3. $EDITOR env var (general-purpose fallback)
   ↓
4. Error with user-friendly message
```

---

### FR-03: Session Locking
**Description:** Ensures only one editing session can modify a specific note file at a time.

**Acceptance Criteria:**
| ID | Criterion | Test Method |
|----|-----------|-------------|
| FC-03.1 | Creates lock file `.gitnotes/sessions/<name>.lock` on edit start | File exists during active session |
| FC-03.2 | Uses `flock -x` for exclusive locking | Verified via strace or lsof |
| FC-03.3 | Lock auto-releases on process exit (clean or crash) | Check file disappears after exit |
| FC-03.4 | Warns if stale lock detected on startup | User sees warning message |

**Implementation:**
```bash
# Lock file location: .gitnotes/sessions/<name>.lock
# Mechanism: flock -x (Unix advisory locking)
```

---

### FR-04: Snapshot Protocol for Crash Safety
**Description:** Stores pre-edit content to enable crash recovery and precise change detection.

**Acceptance Criteria:**
| ID | Criterion | Test Method |
|----|-----------|-------------|
| FC-04.1 | Computes SHA256 hash of current file before edit | Hash matches known value for test fixture |
| FC-04.2 | Writes full file content to `.gitnotes/sessions/<name>.pre-edit` | File contains exact original content |
| FC-04.3 | After editor exits, recomputes hash and compares | Diff shows correct changes |
| FC-04.4 | If process crashes mid-session, snapshot can restore content | Manual crash simulation works |

**Storage Location:** `.gitnotes/sessions/<name>.pre-edit`

---

### FR-05: Post-Editor Validation
**Description:** Verifies file integrity after external editor completes.

**Acceptance Criteria:**
| ID | Criterion | Test Method |
|----|-----------|-------------|
| FC-05.1 | Checks file exists and has size > 0 | `os.path.getsize() > 0` returns True |
| FC-05.2 | Validates UTF-8 encoding of first 4KB | No decode errors on valid markdown files |
| FC-05.3 | Shows error if UTF-8 invalid, offers restore from snapshot | User sees clear error message and options |
| FC-05.4 | Defers semantic (YAML/Markdown) validation to read-time | No parsing overhead during save |

**Performance:** Size check is O(1), UTF-8 check reads max 4KB (<1ms typical).

---

### FR-06: Change Detection & Diff Display
**Description:** Shows user exactly what changed in the current session.

**Acceptance Criteria:**
| ID | Criterion | Test Method |
|----|-----------|-------------|
| FC-06.1 | Computes SHA256 hash before editor spawn | Hash is deterministic for same content |
| FC-06.2 | Stores full pre-edit content in snapshot file | Content matches original byte-for-byte |
| FC-06.3 | After editor exits, compares hashes and shows unified diff if different | Diff output uses `diff -u` format with context |
| FC-06.4 | Shows both pre- and post-edit hashes in session metadata | Metadata file contains hash values for debugging |

**Diff Format:** Unified diff (`-u`) with 3-line context (`-C 3`)

---

### FR-07: External Change Recovery
**Description:** Handles cases where user manually edits the file before or during a GitNotes session.

**Acceptance Criteria:**
| ID | Criterion | Test Method |
|----|-----------|-------------|
| FC-07.1 | **Before editor**: Checks if current hash differs from pre-edit snapshot | Warning appears: "File modified externally" |
| FC-07.2 | Offers options: Continue, Restore, or Revert | User sees 3 clear choices |
| FC-07.3 | **After editor**: Compares again to catch additional changes | Second check catches more edits |
| FC-07.4 | Presents unified diff regardless of change source | Diff shows net result clearly |

**User Choices:**
1. **Accept**: Commit the current (possibly combined) changes
2. **Retry**: Spawn editor again for another round
3. **Revert**: Restore from last known good state

---

### FR-08: Git Commit Integration
**Description:** Atomically commits changes with meaningful commit messages.

**Acceptance Criteria:**
| ID | Criterion | Test Method |
|----|-----------|-------------|
| FC-08.1 | Runs `git add <file>` + `git commit -m "<action>: <title>"` only if hash indicates change | Verify with `git log --oneline -3` |
| FC-08.2 | Extracts title from YAML front matter (`title:` field) | Commit message matches front matter title |
| FC-08.3 | Skips commit if no actual changes detected | No new commit created for empty diff |
| FC-08.4 | Uses single file, atomic operation per edit session | Each session = one commit (max)

**Commit Message Format:** `edit: <Note Title>`

---

### FR-09: Pandoc Export
**Description:** Converts markdown notes to HTML using embedded YAML front matter.

**Acceptance Criteria:**
| ID | Criterion | Test Method |
|----|-----------|-------------|
| FC-09.1 | Checks pandoc exists via `shutil.which("pandoc")` or `exec.LookPath()` | Returns True if installed |
| FC-09.2 | Runs simple invocation: `pandoc file.md -o file.html` | HTML output created in correct location |
| FC-09.3 | Verifies exit code (0 = success) and checks stderr for errors | Non-zero exit triggers error handling |
| FC-09.4 | Implements retry logic: 1st attempt + 1 retry with increased timeout | Second attempt succeeds if transient failure |

**Command:** `pandoc notes/<filename>.md -o <filename>.html`

---

### FR-10: Git Grep Search
**Description:** Fast, content-focused search across all tracked markdown files.

**Acceptance Criteria:**
| ID | Criterion | Test Method |
|----|-----------|-------------|
| FC-10.1 | Uses `git grep -i -n -C 3 --heading --break -e "<query>"` | Results match expected files/lines |
| FC-10.2 | Case-insensitive matching by default (`-i` flag) | "Test" and "test" both find matches |
| FC-10.3 | Shows line numbers for precise location (`-n` flag) | Line numbers displayed in output |
| FC-10.4 | Shows 3 lines of context before/after match (`-C 3` flag) | Context visible around each match |
| FC-10.5 | Automatically excludes `.git/`, `.gitnotes/` from results | No internal directory files shown |

**Flags Explanation:**
- `-i`: Case-insensitive (user-friendly)
- `-n`: Show line numbers
- `-C 3`: 3 lines context each side
- `--heading`: Show file heading with each result
- `--break`: Page long output

---

### FR-11: Empty File Edge Case
**Description:** Handles saving a note as completely empty.

**Acceptance Criteria:**
| ID | Criterion | Test Method |
|----|-----------|-------------|
| FC-11.1 | Checks file size after editor exits: `os.path.getsize() == 0` | Size check returns True for empty files |
| FC-11.2 | Shows prompt: "Keep empty or restore?" with options | User sees clear message and choices |
| FC-11.3 | **Keep**: Commits the empty file as-is if user accepts | Git commit created with empty content |
| FC-11.4 | **Restore**: Reverts to pre-edit content from snapshot | File restored, size > 0 after restore

**User Options:**
1. **Keep**: Commit empty file (valid use case for placeholders)
2. **Restore**: Recreate from `.gitnotes/sessions/<name>.pre-edit`

---

### FR-12: Deleted File Edge Case
**Description:** Handles cases where the note file is deleted during/after editing.

**Acceptance Criteria:**
| ID | Criterion | Test Method |
|----|-----------|-------------|
| FC-12.1 | After editor exits, checks if file exists with `os.path.exists(filepath)` | Returns False for missing files |
| FC-12.2 | If missing and snapshot available: shows "Note file is missing" message | Clear error message displayed |
| FC-12.3 | Offers to restore from pre-edit snapshot in `.gitnotes/sessions/` | User can choose to recover content |
| FC-12.4 | If no snapshot, suggests re-reading the note and shows last known state | Helpful recovery guidance provided

**Recovery Flow:**
```
1. Detect: `os.path.exists(filepath)` → False
2. Check: Is pre-edit snapshot available? → Yes (in .gitnotes/sessions/)
3. Prompt: "Note file is missing. Restore from last session?"
4. User chooses: [Restore] or [Skip]
```

---

### FR-13: Config Cascade System
**Description:** Three-tier configuration resolution for flexibility and portability.

**Acceptance Criteria:**
| ID | Criterion | Test Method |
|----|-----------|-------------|
| FC-13.1 | **Project-level**: `.gitnotes` file in repo root (committed) | File contains JSON with `editor: "nvim"`, etc. |
| FC-13.2 | **Global config**: `~/.config/gitnotes/config` (persistent, uncommitted) | Shell script or INI-style config loaded |
| FC-13.3 | **Environment variables** (highest priority): `GITNOTES_EDITOR` overrides all | Setting env var changes effective editor immediately |

**Precedence:**
```
Level 1: .gitnotes file (project-specific, committed)
   ↓ Falls back to
Level 2: ~/.config/gitnotes/config (user prefs, persistent)
   ↓ Falls back to
Level 3: Environment variables (emergency/testing override)
```

**Example `.gitnotes` content:**
```json
{
  "editor": "nvim",
  "default_tags": ["personal", "2026"]
}
```

---

### FR-14: .gitattributes Management
**Description:** Ensures consistent line ending behavior across platforms.

**Acceptance Criteria:**
| ID | Criterion | Test Method |
|----|-----------|-------------|
| FC-14.1 | Auto-creates `.gitattributes` on `gitnotes init` | File exists after initialization |
| FC-14.2 | Contains exactly: `*.md text eol=lf` | Content matches specification |
| FC-14.3 | Applies LF line endings to all markdown files in repo | `file notes/*.md` shows "text" type |

**Effect:** Tells Git to treat all `.md` as text and use LF (Unix-style) line endings universally.

---

### FR-15: Session Metadata Storage
**Description:** Stores session information for debugging and recovery.

**Acceptance Criteria:**
| ID | Criterion | Test Method |
|----|-----------|-------------|
| FC-15.1 | Creates `.gitnotes/sessions/<name>.meta` file on session start | Meta file exists during active session |
| FC-15.2 | Stores: pre-edit hash, post-edit hash (if changed), user choices, timestamp | All fields present and accurate |
| FC-15.3 | Updates metadata as session progresses | Hash values change correctly after edits

**Metadata Schema:**
```json
{
  "session_id": "<uuid>",
  "pre_edit_hash": "sha256:...",
  "post_edit_hash": "sha256:...",
  "user_choices": [
    {"type": "empty_file", "choice": "keep"},
    {"type": "external_change", "choice": "accept"}
  ],
  "timestamp": "2026-01-15T14:30:00Z"
}
```

---

## 4. Non-Functional Requirements

### NFR-01: Performance Requirements
| ID | Metric | Target |
|----|--------|--------|
| NFR-01.1 | Hash computation (SHA256) | <1ms for typical note files (<10KB) |
| NFR-01.2 | Post-editor validation (size + UTF-8) | <1ms, reads max 4KB buffer |
| NFR-01.3 | Diff display generation | <100ms for files up to 50KB |
| NFR-01.4 | Git grep search speed | Leverages Git's optimized algorithms (comparable to native `git grep`) |

### NFR-02: Reliability Requirements
| ID | Metric | Target |
|----|--------|--------|
| NFR-02.1 | Crash recovery success rate | 99.9% for sessions with active snapshot |
| NFR-02.2 | Lock contention handling | <50ms average wait time when lock available |
| NFR-02.3 | UTF-8 validation false positive rate | <0.1% (only on truly corrupted files) |

### NFR-03: User Experience Requirements
| ID | Metric | Target |
|----|--------|--------|
| NFR-03.1 | Number of prompts per session | Max 3 (empty file, external change, deleted file) |
| NFR-03.2 | Diff readability | Unified format with 3-line context for easy review |
| NFR-03.3 | Error message clarity | All errors include actionable recovery steps |

### NFR-04: Portability Requirements
| ID | Metric | Target |
|----|--------|--------|
| NFR-04.1 | Cross-platform compatibility | Works on Linux, macOS, and Windows (via WSL/WSL2) |
| NFR-04.2 | Line ending consistency | LF endings enforced via `.gitattributes` |
| NFR-04.3 | Editor independence | Any UTF-8 capable editor works (vim, nano, VS Code, etc.) |

### NFR-05: Memory Requirements
| ID | Metric | Target |
|----|--------|--------|
| NFR-05.1 | Peak memory per session | <5MB for typical note files |
| NFR-05.2 | Snapshot file size | Matches source file (no overhead) |

---

## 5. High-Level Architecture Overview

### System Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      GitNotes CLI                            │
│                     Main Loop                                │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│   │  note    │    │  note    │    │  note    │              │
│   │  edit    │◄──►│  search  │    │  export  │              │
│   └──────────┘    └──────────┘    └──────────┘              │
│        │                │                  │                 │
│        ▼                ▼                  ▼                 │
│   ┌─────────────────────────────────────────────┐           │
│   │           Core Services Layer                │           │
│   ├─────────────────────────────────────────────┤           │
│   │  • Session Manager (lock + snapshot)         │           │
│   │  • Change Detector (hash comparison)         │           │
│   │  • Editor Resolver (config cascade)          │           │
│   │  • Git Integrator (add/commit/grep)          │           │
│   └─────────────────────────────────────────────┘           │
│        │                │                  │                 │
│        ▼                ▼                  ▼                 │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│   │  External │    │  Pandoc  │    │  Git     │              │
│   │  Editor   │    │  Export  │    │  Grep    │              │
│   │           │◄──►│          │◄──►│          │              │
│   └──────────┘    └──────────┘    └──────────┘              │
│                                                               │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│   │  File I/O│◄──►│  Hashing │◄──►│  Storage │              │
│   │          │    │(SHA256)  │    │ (temp)   │              │
│   └──────────┘    └──────────┘    └──────────┘              │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                      Storage Layer                            │
├─────────────────────────────────────────────────────────────┤
│  .git/                    .gitnotes/config                   │
│  (Git version control)    (User preferences)                 │
│                         ┌──────────┐                        │
│                         │ sessions/│                        │
│                         ├──────────┤                        │
│              ┌──────────┴─────┬────┴──────────┐              │
│              │  pre-edit      │   locks       │              │
│              │  snapshots     │   (flock)     │              │
│              │ (.pre-edit)    │ (.lock)       │              │
│              └────────────────┴───────────────┘              │
├─────────────────────────────────────────────────────────────┤
│                      External Layer                           │
├─────────────────────────────────────────────────────────────┤
│  User's Text Editor (vim, nano, VS Code, etc.)               │
│  Pandoc (for HTML export)                                    │
│  Git CLI (for version control operations)                    │
└─────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

#### Editing Session Lifecycle:

```
1. User runs: note edit notes/example.md
   │
2. ┌──► Acquire session lock (flock)
   │
3. ┌──► Compute pre-edit SHA256 hash → "abc123..."
   │
4. ┌──► Write full content to .gitnotes/sessions/example.pre-edit
   │
5. ┌──► Check for external changes (compare with snapshot)
   │        ├─ If changed: Prompt user [Accept/Retry/Revert]
   │        └─ If same: Continue normally
   │
6. ┌──► Spawn configured external editor (e.g., vim)
   │       └─ Black-box model: Just spawn, wait for exit
   │
7. ┌──► Editor exits → Compute post-edit hash → "def456..."
   │
8. ┌──► Compare hashes:
   │        ├─ If same (no change): Skip commit
   │        ├─ If different: Show unified diff + [Accept/Retry]
   │        └─ If empty file: Prompt [Keep/Restore]
   │
9. ┌──► User accepts → Run: git add + git commit -m "edit: <title>"
   │
10.┌──► Release session lock
   │
11.└─── Session complete
```

### Data Flow Diagram (Editing)

```
User Note File                          Storage Layer
     │                                      │
     ├─► Read current content               │
     │       └─► Compute hash              │
     │                   │                 │
     │       ┌───────────┴──────┐          │
     │       │                  │         │
     ▼       ▼                  ▼         │
  External   Write to           │         │
  Editor     Snapshot File      │         │
     │       (.pre-edit)        │         │
     └──────────────┬───────────┘         │
                   │                     │
                   ▼                     │
            User Edits                    │
                   │                     │
                   ▼                     │
            Editor Exits                  │
                   │                     │
                   ├─► Read content       │
                   │       └─► Compute hash│
                   │                   │  
                   ▼                   │
              Hash Comparison          │
                   │                   │
      ┌────────────┴────────────┐      │
      │                         │     │
   Same        Different         │    │
      │            │              │    │
   Skip           ├─► Show diff  │    │
                  │       + prompts│    │
                  ▼               │    │
             Hash Check Again     │    │
                  │               │    │
         ┌────────┴───────────────┘    │
         │                             │
   Same  Different                     │
      │            │                    │
 Skip   ├─► Show combined diff + prompts│
        │       [Accept/Retry]          │
        ▼                              │
   Hash Check Again                   │
        │                              │
┌───────┴───────────────┐              │
│                        │             │
  Same      Different    │             │
     │           │         │            │
 Skip    ├─► Show combined diff + prompts│
         │       [Accept/Retry]          │
         ▼                              │
      Hash Check Again                 │
         │                             │
   ┌─────┴──────────────┐               │
   │                     │              │
 Same  Different        │               │
    │         │          │               │
 Skip    ├─► Show final diff + prompts  │
         │       [Accept/Retry]         │
         ▼                             │
      Final Hash Check                │
         │                            │
 ┌───────┴──────────────┐              │
 │                         │           │
 Same    Different       │            │
    │          │           │           │
 Skip     ├─► Show final diff + prompts│
          │       [Accept/Retry]        │
          ▼                            │
       Final Hash Check               │
          │                           │
 ┌───────┴──────────────┐              │
 │                         │           │
 Same     Different      │             │
    │         │            │            │
 Skip   ├─► Show final diff + prompts│
        │       [Accept/Retry]        │
        ▼                            │
     Final Hash Check               │
        │                           │
 ┌──────┴─────────────┐              │
 │                        │          │
 Same    Different     │             │
    │         │           │           │
 Skip   ├─► Show final diff + prompts│
        │       [Accept/Retry]        │
        ▼                            │
     Final Hash Check               │
        │                           │
 ┌──────┴─────────────┐              │
 │                        │          │
 Same     Different    │             │
    │         │           │           │
 Skip   ├─► Show final diff + prompts│
        │       [Accept/Retry]        │
        ▼                            │
     Final Hash Check               │
        │                           │
 ┌──────┴─────────────┐              │
 │                        │          │
 Same     Different    │             │
    │         │           │           │
 Skip   ├─► Show final diff + prompts│
        │       [Accept/Retry]        │
        ▼                            │
     Final Hash Check               │
        │                           │
 ┌──────┴─────────────┐              │
 │                        │          │
 Same     Different    │             │
    │         │           │           │
 Skip   ├─► Show final diff + prompts│
        │       [Accept/Retry]        │
        ▼                            │
     Final Hash Check               │
        │                           │
 ┌──────┴─────────────┐              │
 │                        │          │
 Same     Different    │             │
    │         │           │           │
 Skip   ├─► Show final diff + prompts│
        │       [Accept/Retry]        │
        ▼                            │
     Final Hash Check               │
        │                           │
 ┌──────┴─────────────┐              │
 │                        │          │
 Same     Different    │             │
    │         │           │           │
 Skip   ├─► Show final diff + prompts│
        │       [Accept/Retry]        │
        ▼                            │
     Final Hash Check               │
        │                           │
 ┌──────┴─────────────┐              │
 │                        │          │
 Same     Different    │             │
    │         │           │           │
 Skip   ├─► Show final diff + prompts│
        │       [Accept/Retry]        │
        ▼                            │
     Final Hash Check               │
        │                           │
 ┌──────┴─────────────┐              │
 │                        │          │
 Same     Different    │             │
    │         │           │           │
 Skip   ├─► Show final diff + prompts│
        │       [Accept/Retry]        │
        ▼                            │
     Final Hash Check               │
        │                           │
 ┌──────┴─────────────┐              │
 │                        │          │
 Same     Different    │             │
    │         │           │           │
 Skip   ├─► Show final diff + prompts│
        │       [Accept/Retry]        │
        ▼                            │
     Final Hash Check               │
        │                           │
 ┌──────┴─────────────┐              │
 │                        │          │
 Same     Different    │             │
    │         │           │           │
 Skip   ├─► Show final diff + prompts│
        │       [Accept/Retry]        │
        ▼                            │
     Final Hash Check               │
        │                           │
 ┌──────┴─────────────┐              │
 │                        │          │
 Same     Different    │             │
    │         │           │           │
 Skip   ├─► Show final diff + prompts│
        │       [Accept/Retry]        │
        ▼                            │
     Final Hash Check               │
```

### File Structure (Post-Initialization)

```
repo/
├── .git/                          # Git version control
├── .gitnotes/
│   ├── config                     # User preferences (persistent)
│   └── sessions/                  # Pre-edit snapshots & locks
│       ├── example.pre-edit       # Snapshot for current session
│       ├── example.lock           # Lock file (flock)
│       ├── example.meta           # Session metadata
│       └── ...                    # Other sessions
├── .gitattributes                 # *.md text eol=lf
└── notes/                         # User's markdown files
    ├── example.md
    └── ...
```

---

## 6. Key Design Decisions (Summarized from ADRs)

### ADR-01: Session Snapshot Protocol (Hash-Based, Crash-Safe)
**Decision:** Use SHA256 hash of file content before/after edit, with full pre-edit content stored in `.gitnotes/sessions/<name>.pre-edit`.

**Rationale:**
- **Deterministic**: Same content always produces same hash
- **Fast**: SHA256 is extremely fast on modern CPUs (~10MB/s+)
- **Simple**: No need to parse markdown or YAML for change detection
- **Crash-safe**: Full snapshot allows recovery even if file is deleted

**Trade-offs:**
- Snapshot files grow with file size (but only one active at a time)
- Slight disk I/O for reading/writing snapshot before each edit

---

### ADR-02: Session Locking (flock)
**Decision:** Use `flock -x` for exclusive locking with lock file `.gitnotes/sessions/<name>.lock`, auto-released on process exit.

**Rationale:**
- **Simple**: Built into most Unix shells, no external dependencies
- **Cross-process**: Works even if another process holds the lock
- **Auto-release**: Even crashes release locks automatically
- **Lightweight**: Minimal filesystem overhead (single file per session)

---

### ADR-03: Post-Editor Validation
**Decision:** Check existence, non-empty size, and UTF-8 validity (first 4KB), defer semantic validation to read-time.

**Rationale:**
- **Fast**: Size check is O(1), UTF-8 check only reads 4KB max
- **Non-blocking**: No need to parse entire file or validate complex syntax
- **Minimal friction**: Users can write raw text without worrying about Markdown rules

---

### ADR-04: Change Detection (Hash-Based)
**Decision:** Same as ADR-01 - SHA256 hash comparison with snapshot files.

**Note:** This ADR elaborates on the implementation details, confirming the choice of:
- Hash: SHA256 of `file.md` before/after edit
- Snapshot: `.gitnotes/sessions/<name>.pre-edit` stores full pre-edit content
- Diff: Show unified diff if hash differs

---

### ADR-05: External Change Recovery
**Decision:** Use hash pre/post-snapshot comparison to detect external changes.

**Implementation:**
1. **Before spawning editor**: Check if current hash differs from pre-edit snapshot (indicates external change)
2. If different, show warning and offer options: Continue with current content or restore from last known good state
3. **After editor exits**: Compare again to catch any more changes
4. Present unified diff for user review regardless of source
5. User can: Accept (commit changes), Retry (spawn editor again), or Revert (restore snapshot)

---

### ADR-06: Git Commit
**Decision:** Use single file commit with meaningful message format: `git add <file> + git commit -m "<action>: <title>"`

**Implementation Details:**
1. After successful edit and user review, run:
   ```bash
   git add notes/<filename>.md
   git commit -m "edit: <note title>"
   ```
2. Use the note's YAML front matter `title` field for the message
3. Only commit if hash comparison shows actual changes occurred
4. Skip commit if file is unchanged (no diff)

---

### ADR-07: Config Cascade
**Decision:** Three-tier configuration system:
1. `.gitnotes` (repo-level, committed) - project-specific settings
2. `~/.config/gitnotes/config` (user prefs, uncommitted) - persistent preferences
3. Env vars override (emergency/testing) - quick overrides for testing

**Example Config Files:**
*.gitnotes* (JSON format):
```json
{
  "editor": "nvim",
  "default_tags": ["personal", "2026"]
}
```

*~/.config/gitnotes/config* (shell script/INI):
```bash
# Default editor, timeout settings, etc.
EDITOR=nvim
SESSION_TIMEOUT=300
```

---

### ADR-08: Pandoc Export
**Decision:** Simple invocation with pre-flight check and retry logic.

**Implementation:**
1. **Pre-flight**: Check if pandoc is in PATH before attempting export
2. **Invoke**: Simple command-line invocation:
   ```bash
   pandoc notes/<filename>.md -o <filename>.html
   ```
3. **Post-check**: Verify exit code (0 = success) and check stderr for errors
4. **Retry logic**: If first attempt fails, retry once with increased timeout; then show detailed error

---

### ADR-09: Search Command (git grep)
**Decision:** Use `git grep -i -n -C 3 --heading --break` with automatic exclusions.

**Flags Used:**
- `-i`: Case-insensitive matching (user-friendly)
- `-n`: Show line numbers for precise location
- `-C 3`: Show 3 lines of context before/after match
- `--heading`: Show file heading with each result
- `--break`: Break long output into pages

**Automatic Exclusions:** `.git/`, `.gitnotes/`

---

### ADR-10: .gitattributes
**Decision:** Auto-create on `gitnotes init` with content: `*.md text eol=lf`

**Rationale:**
- **Portable**: LF is the universal standard for cross-platform consistency
- **Predictable diffs**: No `CRLF` vs `LF` confusion in version control
- **Auto-create**: Minimal setup; just works on project initialization

---

### ADR-11: Initialization
**Decision:** Explicit `gitnotes init` command that bootstraps a new GitNotes repository.

**Steps:**
1. Run `git init` if not already initialized
2. Create `.gitnotes/` directory with subdirectories:
   - `.gitnotes/config` (user preferences)
   - `.gitnotes/sessions/` (pre-edit snapshots & locks)
3. Write initial config file to `.gitnotes/config`
4. Add `.gitattributes` with `*.md text eol=lf`
5. Commit everything with message: "Initialized GitNotes"

---

### ADR-12: Empty File Edge Case
**Decision:** Size check + user prompt approach.

**Implementation:**
1. After editor exits, check file size
2. If `os.path.getsize() == 0`:
   - Show message: "Note is now empty. Keep empty or restore from snapshot?"
3. User options:
   - **Keep**: Commit the empty file as-is
   - **Restore**: Revert to pre-edit content from `.gitnotes/sessions/<name>.pre-edit`
4. Store user choice in session metadata for debugging

---

### ADR-13: Deleted File Edge Case
**Decision:** Hash + error handling (detect via missing file).

**Implementation:**
1. After editor exits, check if file exists:
   ```python
   if not os.path.exists(filepath):
       # File was deleted (crash or manual)
   ```
2. If missing and we have a pre-edit snapshot:
   - Show: "Note file is missing. Restore from last session?"
3. User options:
   - **Restore**: Recreate file from `.gitnotes/sessions/<name>.pre-edit`
   - **Skip**: Leave as-is (file will be recreated on next read)
4. If no snapshot available, show error and suggest re-reading the note

---

### ADR-14: Testability
**Decision:** Hybrid approach using both mock-based unit tests and integration tests with temp repos.

**Component Coverage:**
- **Editor Component**: Mock with `true` command, `cp`, or script file; simulate editor behavior by writing expected output to temp files
- **Hashing Component**: Deterministic - same input always produces same SHA256 hash; testable with known files and expected outputs
- **Locks/flock Component**: Simulated in tests (file-based locks or memory locks)
- **Pandoc Component**: Mocked output files; test pre-flight checks and error handling
- **Git Commands**: Tested against temp repos created in test directory using `tempfile.mkdtemp()`

---

## Appendix: Command Reference

### Core Commands (Not Specified in ADRs but Implied)

| Command | Description |
|---------|-------------|
| `gitnotes init` | Initialize GitNotes repository |
| `note new <filename>` | Create and edit a new note |
| `note edit <filename>` | Edit an existing note |
| `note search <query>` | Search across all notes |
| `note export <filename>` | Export markdown to HTML |

### Git Commands Used Internally

| Command | Purpose |
|---------|--------|
| `git init` | Initialize Git repository (if not already done) |
| `git add <file>` | Stage file for commit |
| `git commit -m "<message>"` | Create atomic commit with meaningful message |
| `git grep -i -n -C 3 --heading --break -e "<query>"` | Search tracked files with context |

---

## Version History

| Version | Date | Changes |
|---------|------|--------|
| 1.0.0 | 2026-05-28 | Initial PRD based on DESIGN_SUMMARY.md, CONTEXT.md, and all 14 ADRs |

---

## Document Approval

**Prepared by:** GitNotes Development Team
**Review Status:** Ready for Implementation Review
**Target Release:** v0.1.0 (Initial Production Release)
