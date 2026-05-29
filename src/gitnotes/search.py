"""
Search Command

Per ADR-0009:
- git grep -i -n -C 3 --heading --break -e "<query>"
- Exclude .git/, .gitnotes/ from results
"""

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SearchMatch:
    file: str
    line: int
    content: str
    context_before: tuple[str, ...]
    context_after: tuple[str, ...]


@dataclass(frozen=True)
class SearchResult:
    matches: tuple[SearchMatch, ...]
    raw: str
    exit_code: int


def _parse_git_grep_output(raw: str) -> tuple[SearchMatch, ...]:
    if not raw.strip():
        return ()

    lines = raw.splitlines()
    current_file = ""
    raw_matches: list[dict] = []
    current_before: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]
        i += 1

        if not line or line == "--":
            if line == "--":
                current_before = []
            continue

        if not re.match(r"^\d+[:-]", line):
            current_file = line
            current_before = []
            continue

        m = re.match(r"^(\d+)([:-])(.*)$", line)
        if not m:
            continue

        line_num = int(m.group(1))
        sep = m.group(2)
        content = m.group(3)

        if sep == ":":
            after: list[str] = []
            while i < len(lines):
                nl = lines[i]
                nm = re.match(r"^(\d+)([:])(.*)$", nl)
                if nm:
                    break
                cm = re.match(r"^(\d+)[-](.*)$", nl)
                if cm:
                    after.append(cm.group(2))
                    i += 1
                else:
                    break

            raw_matches.append(
                {
                    "file": current_file,
                    "line": line_num,
                    "content": content,
                    "context_before": list(current_before),
                    "context_after": list(after),
                }
            )
            current_before = after
        else:
            current_before.append(content)

    return tuple(
        SearchMatch(
            file=rm["file"],
            line=rm["line"],
            content=rm["content"],
            context_before=tuple(rm["context_before"]),
            context_after=tuple(rm["context_after"]),
        )
        for rm in raw_matches
    )


def search_notes(query: str, context: int = 3) -> SearchResult:
    cmd = [
        "git",
        "grep",
        "-i",
        "-n",
        "-C",
        str(context),
        "--heading",
        "--break",
        "-e",
        query,
        "--",
        ":(exclude).gitnotes/*",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return SearchResult(
        matches=_parse_git_grep_output(result.stdout),
        raw=result.stdout,
        exit_code=result.returncode,
    )
