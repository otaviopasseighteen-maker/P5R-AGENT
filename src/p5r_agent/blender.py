"""Blender discovery helpers; no scripts are executed by this module."""

from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import subprocess


@dataclass(frozen=True)
class BlenderStatus:
    executable: str | None
    available: bool
    version_output: str | None
    error: str | None = None


def find_blender(explicit_path: str | None = None) -> str | None:
    """Find Blender without guessing custom install paths."""
    if explicit_path:
        candidate = Path(explicit_path).expanduser()
        if candidate.is_file():
            return str(candidate.resolve())
        return shutil.which(explicit_path)
    env_path = os.environ.get("BLENDER_EXECUTABLE")
    if env_path:
        candidate = Path(env_path).expanduser()
        if candidate.is_file():
            return str(candidate.resolve())
        found = shutil.which(env_path)
        if found:
            return found
    return shutil.which("blender")


def inspect_blender(explicit_path: str | None = None, timeout: int = 10) -> BlenderStatus:
    """Check whether Blender can launch and report its version."""
    executable = find_blender(explicit_path)
    if not executable:
        return BlenderStatus(None, False, None, "Blender executable not found")
    try:
        result = subprocess.run(
            [executable, "--version"], capture_output=True, text=True,
            timeout=timeout, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return BlenderStatus(executable, False, None, str(exc))
    output = (result.stdout or result.stderr).strip()
    if result.returncode != 0:
        return BlenderStatus(executable, False, output, f"Blender exited with code {result.returncode}")
    return BlenderStatus(executable, True, output)
