"""Basic path-safety and approval policy for the agent."""

from pathlib import Path

READ_ONLY_ACTIONS = frozenset({"scan", "read", "search", "validate", "git_status", "git_diff"})
APPROVAL_REQUIRED_ACTIONS = frozenset({"write", "delete", "commit", "push", "merge", "deploy", "run_blender_script"})


class PolicyError(ValueError):
    """Raised when an operation violates the local safety policy."""


def resolve_workspace_path(workspace: Path, requested: str | Path) -> Path:
    """Resolve a requested path and reject paths outside the workspace."""
    root = workspace.expanduser().resolve()
    candidate = (root / requested).resolve() if not Path(requested).is_absolute() else Path(requested).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise PolicyError(f"Path escapes workspace: {requested}") from exc
    return candidate


def require_approval(action: str, approved: bool = False) -> None:
    """Require explicit approval for any action classified as mutating/high impact."""
    if action in APPROVAL_REQUIRED_ACTIONS and not approved:
        raise PolicyError(f"Approval required for action: {action}")
