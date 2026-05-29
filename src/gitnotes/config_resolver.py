"""
Editor Configuration Resolution

Per DESIGN_SUMMARY:
Choice: A → D fallback chain
- Primary: .gitnotes config file editor key
- Fallback 1: $VISUAL env var (full-screen editors)
- Fallback 2: $EDITOR env var
- Error: Exit with message if none found

Rationale: Clean, explicit user control; respects OS conventions.
"""

import os
from pathlib import Path


def _load_config_file() -> dict:
    """
    Load .gitnotes config file (project-level, committed).
    
    Returns a dict with configuration values, or empty dict if not found.
    The config file would be at repo/.gitnotes/config.toml or similar.
    For now, returns defaults since the file is created empty on init.
    """
    # TODO: Load from .gitnotes/config.toml when it exists
    return {}


def _get_env_var_fallbacks() -> list:
    """
    Get environment variable fallbacks in order of precedence.
    
    Returns a list of (env_name, description) tuples.
    """
    # Fallback 1: $VISUAL (full-screen editors)
    # Fallback 2: $EDITOR
    return [
        ("VISUAL", "$VISUAL env var (full-screen editor)"),
        ("EDITOR", "$EDITOR env var"),
    ]


def resolve_editor() -> str:
    """
    Resolve the configured text editor using cascade precedence.
    
    Precedence chain:
    1. .gitnotes config file (project-level, committed)
    2. $VISUAL env var (full-screen editors)
    3. $EDITOR env var
    4. Error: Exit with message if none found
    
    Returns:
        str: The resolved editor command or path
    """
    # Step 1: Check project-level config file
    config = _load_config_file()
    if config and "editor" in config:
        return config["editor"]
    
    # Step 2: Fallback to $VISUAL
    visual = os.environ.get("VISUAL")
    if visual:
        return visual
    
    # Step 3: Fallback to $EDITOR
    editor = os.environ.get("EDITOR")
    if editor:
        return editor
    
    # Step 4: No editor found - provide helpful error
    fallbacks = _get_env_var_fallbacks()
    msg_lines = [
        f"No editor configured. Set one of the following environment variables:",
        f"\n  {fallbacks[0][1]} -> will use '{fallbacks[0][0]}'",
        f"\n  {fallbacks[1][1]} -> will use '{fallbacks[1][0]}'",
        f"\nOr add 'editor = \"your-editor\"' to .gitnotes/config.toml.",
    ]
    msg = "\n".join(msg_lines)
    
    print(msg)
    raise RuntimeError("No editor configured")
