"""Reviewable, explicit-approval workflow for bounded text-file changes.

This module never executes commands. Proposals are stored outside the target
workspace, are tied to the exact current file hash, and can only be applied
after an explicit approval call. The caller must expose approval through a
deliberate UI action, not from model output.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any
from uuid import uuid4

from .policy import PolicyError, resolve_workspace_path

MAX_TEXT_BYTES = 1_000_000
ALLOWED_SUFFIXES = frozenset({
    ".html", ".htm", ".css", ".js", ".mjs", ".ts", ".tsx", ".jsx",
    ".json", ".md", ".txt", ".py", ".toml", ".yml", ".yaml", ".svg",
})
DENIED_NAMES = frozenset({".env", ".env.local", ".env.production", "credentials.json"})
ID_RE = re.compile(r"^[a-f0-9]{32}$")


@dataclass(frozen=True)
class ChangeProposal:
    proposal_id: str
    path: str
    reason: str
    before_sha256: str
    after_sha256: str
    created_at: str
    status: str
    preview: str


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _state_root(state_dir: Path | None = None) -> Path:
    root = state_dir or (Path.home() / ".p5r-agent" / "state")
    root = root.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _proposal_path(state: Path, proposal_id: str) -> Path:
    if not ID_RE.fullmatch(proposal_id):
        raise PolicyError("Invalid proposal ID.")
    return state / "proposals" / f"{proposal_id}.json"


def _read_proposal(state: Path, proposal_id: str) -> dict[str, Any]:
    path = _proposal_path(state, proposal_id)
    if not path.is_file():
        raise FileNotFoundError(f"Proposal not found: {proposal_id}")
    record = json.loads(path.read_text(encoding="utf-8"))
    if record.get("proposal_id") != proposal_id:
        raise PolicyError("Proposal record identity mismatch.")
    return record


def list_proposals(state_dir: Path | None = None) -> list[dict[str, Any]]:
    state = _state_root(state_dir)
    folder = state / "proposals"
    if not folder.exists():
        return []
    items = []
    for path in sorted(folder.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        # Do not return proposed file contents through the listing endpoint.
        item.pop("content", None)
        items.append(item)
    return items


def create_proposal(
    workspace: Path,
    requested_path: str,
    proposed_content: str,
    reason: str,
    state_dir: Path | None = None,
) -> ChangeProposal:
    """Create a proposal for an existing, bounded UTF-8 text file; write nothing to workspace."""
    if not isinstance(proposed_content, str):
        raise PolicyError("Proposed content must be text.")
    if not isinstance(reason, str) or not reason.strip() or len(reason) > 1000:
        raise PolicyError("Provide a short reason (up to 1000 characters).")
    if len(proposed_content.encode("utf-8")) > MAX_TEXT_BYTES:
        raise PolicyError(f"Proposed file exceeds {MAX_TEXT_BYTES} bytes.")
    root = workspace.expanduser().resolve()
    target = resolve_workspace_path(root, requested_path)
    if target.name.lower() in DENIED_NAMES or target.suffix.lower() not in ALLOWED_SUFFIXES:
        raise PolicyError("This file type is not allowed for proposed edits.")
    if not target.is_file():
        raise PolicyError("Only existing files can be proposed for editing; new files are not supported yet.")
    current = target.read_bytes()
    if len(current) > MAX_TEXT_BYTES:
        raise PolicyError(f"Current file exceeds {MAX_TEXT_BYTES} bytes.")
    try:
        current.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PolicyError("Only UTF-8 text files can be proposed for editing.") from exc

    proposal_id = uuid4().hex
    record = {
        "proposal_id": proposal_id,
        "path": target.relative_to(root).as_posix(),
        "reason": reason.strip(),
        "before_sha256": _sha256(current),
        "after_sha256": _sha256(proposed_content.encode("utf-8")),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "pending",
        "preview": proposed_content[:1200],
        "content": proposed_content,
    }
    state = _state_root(state_dir)
    folder = state / "proposals"
    folder.mkdir(parents=True, exist_ok=True)
    proposal_file = _proposal_path(state, proposal_id)
    proposal_file.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return ChangeProposal(**{key: record[key] for key in ChangeProposal.__dataclass_fields__})


def reject_proposal(proposal_id: str, state_dir: Path | None = None) -> dict[str, str]:
    state = _state_root(state_dir)
    record = _read_proposal(state, proposal_id)
    if record["status"] != "pending":
        raise PolicyError(f"Proposal is not pending (status: {record['status']}).")
    record["status"] = "rejected"
    record.pop("content", None)
    _proposal_path(state, proposal_id).write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"proposal_id": proposal_id, "status": "rejected"}


def approve_and_apply(
    workspace: Path,
    proposal_id: str,
    *,
    approved: bool = False,
    state_dir: Path | None = None,
) -> dict[str, str]:
    """Apply one exact pending proposal only after explicit approval and stale-file checks."""
    if approved is not True:
        raise PolicyError("Explicit approval is required.")
    root = workspace.expanduser().resolve()
    state = _state_root(state_dir)
    record = _read_proposal(state, proposal_id)
    if record["status"] != "pending":
        raise PolicyError(f"Proposal is not pending (status: {record['status']}).")
    target = resolve_workspace_path(root, record["path"])
    if not target.is_file():
        raise PolicyError("Target file no longer exists; create a new proposal.")
    current = target.read_bytes()
    if _sha256(current) != record["before_sha256"]:
        raise PolicyError("Target changed after proposal creation. No files were changed; create a fresh proposal.")
    content = record.get("content")
    if not isinstance(content, str) or _sha256(content.encode("utf-8")) != record["after_sha256"]:
        raise PolicyError("Proposal content integrity check failed.")
    if target.name.lower() in DENIED_NAMES or target.suffix.lower() not in ALLOWED_SUFFIXES:
        raise PolicyError("This file type is not allowed for proposed edits.")

    backup_dir = state / "backups" / proposal_id
    backup_dir.mkdir(parents=True, exist_ok=False)
    backup = backup_dir / target.name
    shutil.copy2(target, backup)
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", dir=target.parent, delete=False) as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
            temporary = handle.name
        os.replace(temporary, target)
        temporary = None
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)

    record["status"] = "applied"
    record["backup_path"] = str(backup)
    record.pop("content", None)
    _proposal_path(state, proposal_id).write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"proposal_id": proposal_id, "status": "applied", "path": record["path"], "backup_path": str(backup)}
