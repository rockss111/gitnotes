"""
Pandoc Export

Per ADR-0008:
- pandoc file.md -o file.html
- Pre-flight: shutil.which("pandoc")
- Post-check: exit code + stderr
- Retry: once with increased timeout on failure
"""

import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExportResult:
    success: bool
    exit_code: int | None
    stderr: str
    output_path: Path | None


def check_pandoc(pandoc_path: str = "pandoc") -> bool:
    return shutil.which(pandoc_path) is not None


def export_note(
    note_path: Path, *, pandoc_path: str = "pandoc", fmt: str = "html"
) -> ExportResult:
    if not check_pandoc(pandoc_path):
        return ExportResult(
            success=False,
            exit_code=None,
            stderr="pandoc not found in PATH",
            output_path=None,
        )

    output_path = note_path.with_suffix(f".{fmt}")
    timeouts = [30, 60]
    last_result: subprocess.CompletedProcess | None = None
    last_error = ""

    for attempt, timeout in enumerate(timeouts):
        try:
            last_result = subprocess.run(
                [pandoc_path, str(note_path), "-o", str(output_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if last_result.returncode == 0:
                return ExportResult(
                    success=True,
                    exit_code=0,
                    stderr=last_result.stderr,
                    output_path=output_path,
                )
            if attempt < len(timeouts) - 1:
                time.sleep(0.5)
        except subprocess.TimeoutExpired as e:
            last_error = str(e)
            if attempt < len(timeouts) - 1:
                time.sleep(0.5)
                continue
            return ExportResult(
                success=False,
                exit_code=None,
                stderr=f"pandoc timed out: {last_error}",
                output_path=output_path,
            )

    return ExportResult(
        success=False,
        exit_code=last_result.returncode if last_result is not None else None,
        stderr=last_result.stderr if last_result is not None else last_error,
        output_path=output_path,
    )
