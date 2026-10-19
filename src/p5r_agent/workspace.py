"""Read-only workspace inspection helpers."""

from pathlib import Path
from typing import Iterable

from .policy import resolve_workspace_path


DEFAULT_IGNORED_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__", "dist", "build"
}


def scan_files(workspace: Path, ignored_dirs: Iterable[str] = DEFAULT_IGNORED_DIRS) -> list[str]:
    """List relative file paths while skipping common generated/vendor directories."""
    root = workspace.expanduser().resolve()
    if not root.is_dir():
        raise NotADirectoryError(f"Workspace is not a directory: {root}")
    ignored = set(ignored_dirs)
    results: list[str] = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part in ignored for part in relative.parts):
            continue
        if path.is_file():
            results.append(relative.as_posix())
    return sorted(results)


def read_text(workspace: Path, requested: str | Path, max_bytes: int = 1_000_000) -> str:
    """Read a UTF-8 text file inside the workspace with a size limit."""
    path = resolve_workspace_path(workspace, requested)
    if not path.is_file():
        raise FileNotFoundError(path)
    if path.stat().st_size > max_bytes:
        raise ValueError(f"File exceeds read limit ({max_bytes} bytes): {requested}")
    return path.read_text(encoding="utf-8")


def search_text(workspace: Path, query: str, extensions: set[str] | None = None) -> list[dict[str, str | int]]:
    """Search text files, returning relative path and 1-based line number."""
    if not query:
        raise ValueError("query must not be empty")
    root = workspace.expanduser().resolve()
    hits: list[dict[str, str | int]] = []
    for relative in scan_files(root):
        path = root / relative
        if extensions and path.suffix.lower() not in extensions:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for number, line in enumerate(content.splitlines(), start=1):
            if query.casefold() in line.casefold():
                hits.append({"path": relative, "line": number, "text": line.strip()[:300]})
    return hits
