"""
Search Command

Per ADR-0009:
- git grep -i -n -C 3 --heading --break -e "<query>"
- Exclude .git/, .gitnotes/ from results
"""

import subprocess
from pathlib import Path


def search_notes(query: str) -> str:
    """
    Search across all tracked notes using git grep.

    Args:
        query: Search string or pattern

    Returns:
        str: Formatted git grep output, or empty string if no matches
    """
    cmd = [
        "git", "grep",
        "-i",
        "-n",
        "-C", "3",
        "--heading",
        "--break",
        "-e", query,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout
