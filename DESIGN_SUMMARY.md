GitNotes Design Summary
Core Contract
Black-box editor integration: Spawn configured editor, wait for exit, detect changes via SHA256 hash comparison.
1. Editor Configuration (Precedence Chain)
Choice: A → D fallback chain
- Primary: .gitnotes config file editor key
- Fallback 1: $VISUAL env var (full-screen editors)
- Fallback 2: $EDITOR env var
- Error: Exit with message if none found
Rationale: Clean, explicit user control; respects OS conventions.
2. Post-Editor Validation
Choice: B + UTF-8 check
- File must exist, be non-empty, and valid UTF-8
- Semantic (YAML/Markdown) validation deferred to read-time
Rationale: Fast, non-blocking save; minimal friction.
3. Change Detection
Choice: B + snapshot file
- Hash: SHA256 of file.md before/after edit
- Snapshot: .gitnotes/sessions/<name>.pre-edit (crash-safe)
- Diff: Show unified diff if hash differs
Rationale: Precise "what changed in this session" signal.
4. Session Locking
Choice: A (flock)
- Lock file: .gitnotes/sessions/<name>.lock
- Auto-released on process exit (clean or crash)
Rationale: Simple, cross-process mutual exclusion.
5. External Change Recovery
Choice: A (hash pre/post-snapshot)
- Pre-editor check: Hash file vs. snapshot; if different, warn user
- Post-editor check: Compare again after editor exits
- User choice: Accept diff, retry edit, or revert
Rationale: Transparent to user; no silent corruption.
6. Git Commit
Choice: C (single file, meaningful message)
- git add <file> + git commit -m "<action>: <title>"
- Only if hash indicates change
Rationale: Clean, atomic, commit-per-action history.
7. Config Cascade
Choice: A (project → global → env)
- .gitnotes (repo-level, committed)
- ~/.config/gitnotes/config (user prefs, uncommitted)
- Env vars override (emergency testing)
Rationale: Portable + persistent configuration.
8. Pandoc Export
Choice: A (simple invocation) + B (pre-flight check)
- pandoc file.md -o file.html
- Pre-check: shutil.which("pandoc") or exec.LookPath
- Post-check: Exit code + stderr; retry on failure
Rationale: Leverages embedded YAML front matter.
9. Search
Choice: C (git grep with context)
- git grep -i -n -C 3 --heading --break -e "<query>"
- Exclude .git/, .gitnotes/
Rationale: Fast, content-focused, readable.
10. .gitattributes
Choice: A (*.md text eol=lf)
- Auto-create on gitnotes init
- Ensures LF line endings across platforms
Rationale: Portability, predictable diffs.
11. Initialization
Choice: A (gitnotes init command)
- git init, create .gitnotes/, write config, add .gitattributes
- Initial commit: "Initialized GitNotes"
Rationale: Explicit setup, clean repo state.
12. Empty File Edge Case
Choice: A (size check + user prompt)
- If size == 0 after editor: ask "Keep empty or restore?"
- Committed if user accepts
Rationale: Explicit, non-destructive.
13. Deleted File Edge Case
Choice: A (hash + error handling)
- If file missing post-edit: show snapshot, offer restore
- Clean recovery from crash/state mismatch
Rationale: Crash-safe, non-destructive.
14. Testability
- Editor: Mock with true, cp, or script
- Hashing: Deterministic, testable with known files
- Locks/flock: Simulated in tests
- Pandoc: Mocked output files
- Git commands: Tested against temp repos
File Structure (Post-Init)
repo/
├── .git/
├── .gitnotes/
│   ├── config
│   └── sessions/          # pre-edit snapshots & locks
├── .gitattributes         # *.md text eol=lf
└── notes/                 # user's markdown files
Final ADRs (if needed)
- Session snapshot protocol (hash-based, crash-safe)
- Config cascade (project → global → env)
All edge cases covered, all dependencies checked, all failure modes handled. Ready to implement.
