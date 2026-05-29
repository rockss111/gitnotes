"""
Editor Configuration Resolution

Three-tier cascade per ADR-0007:
1. GITNOTES_EDITOR env var (highest priority, emergency/testing override)
2. .gitnotes/config (project-level, committed, travels with repo)
3. ~/.config/gitnotes/config (global, uncommitted, user preferences)
4. $VISUAL (Unix convention fallback)
5. $EDITOR (Unix convention fallback)
6. Error with helpful message
"""

import json
import os
from pathlib import Path


def _load_project_config(repo_path: Path) -> dict:
    config_path = repo_path / ".gitnotes" / "config"
    try:
        data = json.loads(config_path.read_text())
        return data if isinstance(data, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def _load_global_config() -> dict:
    config_path = Path.home() / ".config" / "gitnotes" / "config"
    try:
        data = json.loads(config_path.read_text())
        return data if isinstance(data, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def _get_env_var_fallbacks() -> list:
    return [
        ("GITNOTES_EDITOR", "$GITNOTES_EDITOR env var (override)"),
        ("VISUAL", "$VISUAL env var (full-screen editor)"),
        ("EDITOR", "$EDITOR env var"),
    ]


def resolve_editor(repo_path: Path | None = None) -> str:
    repo_path = repo_path or Path.cwd()

    # Tier 1: GITNOTES_EDITOR env var (highest priority)
    gitnotes_editor = os.environ.get("GITNOTES_EDITOR")
    if gitnotes_editor:
        return gitnotes_editor

    # Tier 2: Project-level .gitnotes/config (committed)
    config = _load_project_config(repo_path)
    if config and "editor" in config:
        return config["editor"]

    # Tier 3: Global ~/.config/gitnotes/config (user preferences)
    global_config = _load_global_config()
    if global_config and "editor" in global_config:
        return global_config["editor"]

    # Fallback 1: $VISUAL (Unix convention)
    visual = os.environ.get("VISUAL")
    if visual:
        return visual

    # Fallback 2: $EDITOR (Unix convention)
    editor = os.environ.get("EDITOR")
    if editor:
        return editor

    # No editor found
    fallbacks = _get_env_var_fallbacks()
    msg_lines = [
        "No editor configured. Set one of the following:",
        f"\n  {fallbacks[0][1]} -> will use '${fallbacks[0][0]}'",
        f"\n  {fallbacks[1][1]} -> will use '${fallbacks[1][0]}'",
        f"\n  {fallbacks[2][1]} -> will use '${fallbacks[2][0]}'",
        "\nOr add '\"editor\": \"your-editor\"' to .gitnotes/config.",
    ]
    msg = "".join(msg_lines)

    print(msg)
    raise RuntimeError("No editor configured")
