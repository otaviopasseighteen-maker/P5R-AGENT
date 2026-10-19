from pathlib import Path

import pytest

from p5r_agent.policy import PolicyError
from p5r_agent.proposals import approve_and_apply, create_proposal, list_proposals, reject_proposal


def test_proposal_does_not_modify_file_until_approved(tmp_path: Path) -> None:
    workspace = tmp_path / "site"
    workspace.mkdir()
    target = workspace / "index.html"
    target.write_text("<h1>old</h1>", encoding="utf-8")
    state = tmp_path / "state"

    proposal = create_proposal(workspace, "index.html", "<h1>new</h1>", "Update heading", state)

    assert target.read_text(encoding="utf-8") == "<h1>old</h1>"
    assert proposal.status == "pending"
    assert list_proposals(state)[0]["proposal_id"] == proposal.proposal_id


def test_apply_requires_explicit_approval_and_creates_backup(tmp_path: Path) -> None:
    workspace = tmp_path / "site"
    workspace.mkdir()
    target = workspace / "index.html"
    target.write_text("<h1>old</h1>", encoding="utf-8")
    state = tmp_path / "state"
    proposal = create_proposal(workspace, "index.html", "<h1>new</h1>", "Update heading", state)

    with pytest.raises(PolicyError):
        approve_and_apply(workspace, proposal.proposal_id, state_dir=state)

    result = approve_and_apply(workspace, proposal.proposal_id, approved=True, state_dir=state)

    assert target.read_text(encoding="utf-8") == "<h1>new</h1>"
    assert Path(result["backup_path"]).read_text(encoding="utf-8") == "<h1>old</h1>"
    assert result["status"] == "applied"


def test_stale_proposal_is_rejected_without_overwriting_newer_file(tmp_path: Path) -> None:
    workspace = tmp_path / "site"
    workspace.mkdir()
    target = workspace / "index.html"
    target.write_text("version one", encoding="utf-8")
    state = tmp_path / "state"
    proposal = create_proposal(workspace, "index.html", "agent version", "Proposed edit", state)
    target.write_text("user edit", encoding="utf-8")

    with pytest.raises(PolicyError, match="Target changed"):
        approve_and_apply(workspace, proposal.proposal_id, approved=True, state_dir=state)

    assert target.read_text(encoding="utf-8") == "user edit"


def test_reject_and_disallow_secret_files(tmp_path: Path) -> None:
    workspace = tmp_path / "site"
    workspace.mkdir()
    (workspace / ".env").write_text("SECRET=x", encoding="utf-8")
    (workspace / "index.html").write_text("hello", encoding="utf-8")
    state = tmp_path / "state"

    with pytest.raises(PolicyError):
        create_proposal(workspace, ".env", "SECRET=y", "Change secret", state)

    proposal = create_proposal(workspace, "index.html", "hello world", "Edit copy", state)
    result = reject_proposal(proposal.proposal_id, state)
    assert result["status"] == "rejected"
    with pytest.raises(PolicyError):
        approve_and_apply(workspace, proposal.proposal_id, approved=True, state_dir=state)
