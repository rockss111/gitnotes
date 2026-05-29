#!/bin/bash

# Create Issue 1: Repository Initialization
cat << 'ISSUE1' > /tmp/issue-1.md
## Parent
None

## What to build
`gitnotes init` command that bootstraps a new GitNotes repository. Creates `.git/`, `.gitnotes/config`, `.gitnotes/sessions/`, and `.gitattributes` with `*.md text eol=lf`. Initial commit with message "Initialized GitNotes".

## Acceptance criteria
- [ ] `.git/` directory exists after initialization
- [ ] `.gitnotes/config` file created (empty or default config)
- [ ] `.gitattributes` contains exactly `*.md text eol=lf`
- [ ] Initial commit exists in git log with message "Initialized GitNotes"

## Blocked by
None - can start immediately

## User stories covered
US-08, US-09
ISSUE1

gh issue create --repo rockss111/gitnotes \
  --title "Slice 1: Repository Initialization" \
  --label "priority:high,feature,ready-for-agent" \
  --body-file /tmp/issue-1.md

# Create Issue 2a: Session Locking & Snapshot Protocol
cat << 'ISSUE2A' > /tmp/issue-2a.md
## Parent
None

## What to build
**Session locking**: `flock -x` on `.gitnotes/sessions/<name>.lock`, auto-release on process exit.
**Snapshot protocol**: Pre-edit SHA256 hash computation, full content write to `.gitnotes/sessions/<name>.pre-edit`.
**Post-edit comparison**: Hash recomputation after editor exits, unified diff generation if changed.

## Acceptance criteria
- [ ] Lock file exists during active session (`flock -x` used)
- [ ] Pre-edit snapshot saved to `.gitnotes/sessions/<name>.pre-edit` with full content
- [ ] Post-edit hash comparison detects changes accurately
- [ ] Unified diff shown when content differs

## Blocked by
Slice 1 (Repository Initialization)

## User stories covered
US-01, US-03, US-04
ISSUE2A

gh issue create --repo rockss111/gitnotes \
  --title "Slice 2a: Session Locking & Snapshot Protocol" \
  --label "priority:high,feature,ready-for-agent" \
  --body-file /tmp/issue-2a.md

# Create Issue 2b: Editor Spawn, Validation & Commit Integration
cat << 'ISSUE2B' > /tmp/issue-2b.md
## Parent
None

## What to build
**Editor spawn**: Config cascade resolution (`.gitnotes` → `~/.config/gitnotes/config` → env vars).
**Post-edit validation**: File existence check, non-empty size check, UTF-8 validity check (first 4KB).
**Commit integration**: `git add <file>` + `git commit -m "edit: <title>"` only if hash indicates change.

## Acceptance criteria
- [ ] Editor spawned using resolved config (project → global → env var precedence)
- [ ] After editor exits, file existence and size validated
- [ ] UTF-8 validity checked on first 4KB; error + snapshot restore option shown if invalid
- [ ] Commit created only when hash differs; message format `edit: <note title>` from YAML front matter

## Blocked by
Slice 1 (Repository Initialization)

## User stories covered
US-01, US-02, US-05, US-07, US-10
ISSUE2B

gh issue create --repo rockss111/gitnotes \
  --title "Slice 2b: Editor Spawn, Validation & Commit Integration" \
  --label "priority:high,feature,ready-for-agent" \
  --body-file /tmp/issue-2b.md

# Create Issue 3: External Change Recovery
cat << 'ISSUE3' > /tmp/issue-3.md
## Parent
None

## What to build
Pre-editor check: Compare current file hash vs pre-edit snapshot; if different, warn user.
Post-editor check: Compare again after editor exits to catch additional changes.
User choice flow: Accept (commit combined changes), Retry (spawn editor again), Revert (restore snapshot).

## Acceptance criteria
- [ ] Before spawning editor, detect external change via hash mismatch
- [ ] If changed, show warning with options: Continue/Restore/Revert
- [ ] After editor exits, perform second comparison to catch more changes
- [ ] Present unified diff regardless of change source; user can accept/retry/revert

## Blocked by
Slice 2a (Session Locking & Snapshot Protocol)

## User stories covered
US-05
ISSUE3

gh issue create --repo rockss111/gitnotes \
  --title "Slice 3: External Change Recovery" \
  --label "priority:high,feature,ready-for-agent" \
  --body-file /tmp/issue-3.md

# Create Issue 4: Edge Cases (Empty & Deleted Files)
cat << 'ISSUE4' > /tmp/issue-4.md
## Parent
None

## What to build
**Empty file handling**: After editor exits, check if size == 0; prompt "Keep empty or restore?" with options to commit empty or restore from snapshot.
**Deleted file recovery**: If file missing post-edit and snapshot exists, offer restore option.

## Acceptance criteria
- [ ] File size checked after editor exits; if zero, prompt user with keep/restore options
- [ ] If file deleted during session and snapshot available, show "Note file is missing" message + restore option
- [ ] User choice recorded in session metadata for debugging

## Blocked by
Slice 1 (Repository Initialization)

## User stories covered
US-01 (partial), US-11, US-12
ISSUE4

gh issue create --repo rockss111/gitnotes \
  --title "Slice 4: Edge Cases (Empty & Deleted Files)" \
  --label "priority:high,feature,ready-for-agent" \
  --body-file /tmp/issue-4.md

# Create Issue 5: Export & Search Features
cat << 'ISSUE5' > /tmp/issue-5.md
## Parent
None

## What to build
**Export**: `note export <filename>` using Pandoc; pre-flight check (`shutil.which`), retry logic on failure.
**Search**: `note search <query>` using `git grep -i -n -C 3 --heading --break`; exclude `.git/`, `.gitnotes/`.

## Acceptance criteria
- [ ] Export checks pandoc exists before running; retries once with increased timeout on failure
- [ ] Search uses correct flags: `-i -n -C 3 --heading --break`
- [ ] Search results automatically exclude internal directories (`.git/`, `.gitnotes/`)

## Blocked by
Slice 1 (Repository Initialization)

## User stories covered
US-06, US-07
ISSUE5

gh issue create --repo rockss111/gitnotes \
  --title "Slice 5: Export & Search Features" \
  --label "priority:high,feature,ready-for-agent" \
  --body-file /tmp/issue-5.md

echo ""
echo "========================================="
echo "Created 5 issues successfully!"
echo "========================================="
rm /tmp/issue-*.md
