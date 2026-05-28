# Config Cascade

## Status
Accepted

## Context
GitNotes needs a flexible configuration system that works both during development and in production, with options for portable testing.

We considered several approaches:
- **A**: Project → Global → Env (three-tier cascade)
- **B**: Environment variables only
- **C**: JSON file config only

## Decision
**Choice: A (project → global → env)**

- `.gitnotes` (repo-level, committed) - project-specific settings
- `~/.config/gitnotes/config` (user prefs, uncommitted) - persistent preferences
- Env vars override (emergency/testing) - quick overrides for testing

### Implementation Details
1. **Project-level** (`.gitnotes` file in repo root):
   ```json
   {
     "editor": "nvim",
     "default_tags": ["personal", "2026"]
   }
   ```
2. **Global config** (`~/.config/gitnotes/config`):
   ```bash
   # Default editor, timeout settings, etc.
   EDITOR=nvim
   SESSION_TIMEOUT=300
   ```
3. **Environment variables** (highest priority):
   - `GITNOTES_EDITOR` overrides project config
   - Used for quick testing without file changes

### Why Three-Tiers?
- **Portable**: Project-specific settings travel with the repo
- **Persistent**: User preferences persist across projects
- **Flexible**: Env vars allow quick overrides (testing, CI)

## Consequences

### Positive
- Portable configuration: Settings travel with the repo
- Persistent user prefs: Don't repeat config every project
- Flexible testing: Quick overrides without file changes
- Clean separation: Project needs vs. user preferences

### Negative
- Slightly more complex resolution logic (3 levels to check)
- Users might expect only 1 or 2 tiers, not 3

### Future Implications
- Can add more tiers if needed (e.g., command-line flags)
- Cascade pattern is well-understood and extensible