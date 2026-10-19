"""Small validators for common website project files."""

import json
import re
from pathlib import Path
from urllib.parse import urlparse

from .policy import resolve_workspace_path


HREF_RE = re.compile(r"""\b(?:href|src)\s*=\s*["']([^"'#]+)["']""", re.IGNORECASE)


def validate_json_files(workspace: Path) -> list[dict[str, str]]:
    """Validate every JSON file found in a workspace."""
    root = workspace.expanduser().resolve()
    issues: list[dict[str, str]] = []
    for relative in root.rglob("*.json"):
        if any(part in {".git", "node_modules", ".venv", "venv"} for part in relative.relative_to(root).parts):
            continue
        try:
            json.loads(relative.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError, OSError) as exc:
            issues.append({"path": relative.relative_to(root).as_posix(), "error": str(exc)})
    return issues


def validate_local_html_links(workspace: Path) -> list[dict[str, str]]:
    """Check relative href/src paths in HTML files; this is intentionally a basic checker."""
    root = workspace.expanduser().resolve()
    issues: list[dict[str, str]] = []
    for html in root.rglob("*.html"):
        relative_html = html.relative_to(root)
        if any(part in {".git", "node_modules", ".venv", "venv"} for part in relative_html.parts):
            continue
        try:
            content = html.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as exc:
            issues.append({"path": relative_html.as_posix(), "error": f"Could not read HTML: {exc}"})
            continue
        for target in HREF_RE.findall(content):
            parsed = urlparse(target)
            if parsed.scheme or target.startswith("//") or target.startswith("data:"):
                continue
            clean_target = target.split("?", 1)[0]
            if not clean_target:
                continue
            base = html.parent if not clean_target.startswith("/") else root
            local = clean_target.lstrip("/") if clean_target.startswith("/") else clean_target
            candidate = (base / local).resolve()
            try:
                candidate.relative_to(root)
            except ValueError:
                issues.append({"path": relative_html.as_posix(), "error": f"Link escapes workspace: {target}"})
                continue
            if not candidate.exists():
                issues.append({"path": relative_html.as_posix(), "error": f"Missing local target: {target}"})
    return issues


def validate_workspace(workspace: Path) -> dict[str, list[dict[str, str]]]:
    return {
        "json": validate_json_files(workspace),
        "html_links": validate_local_html_links(workspace),
    }
