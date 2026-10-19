from pathlib import Path

import pytest

from p5r_agent.policy import PolicyError, require_approval, resolve_workspace_path
from p5r_agent.workspace import read_text, scan_files, search_text


def test_scan_and_read(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("<h1>P5R</h1>", encoding="utf-8")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "hidden").write_text("ignored", encoding="utf-8")

    assert scan_files(tmp_path) == ["index.html"]
    assert "P5R" in read_text(tmp_path, "index.html")


def test_search_text(tmp_path: Path) -> None:
    (tmp_path / "app.js").write_text("const persona = 'Joker';\n", encoding="utf-8")
    assert search_text(tmp_path, "joker")[0]["path"] == "app.js"


def test_reject_path_escape(tmp_path: Path) -> None:
    with pytest.raises(PolicyError):
        resolve_workspace_path(tmp_path, "../outside.txt")


def test_mutation_requires_approval() -> None:
    with pytest.raises(PolicyError):
        require_approval("delete")
    require_approval("delete", approved=True)
