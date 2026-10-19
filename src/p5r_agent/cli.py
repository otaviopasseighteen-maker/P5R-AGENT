"""Command-line entry point for the initial P5R agent foundation."""

import argparse
import json
import subprocess
from pathlib import Path

from .validator import validate_workspace
from .workspace import scan_files, search_text


def _git(workspace: Path, *args: str) -> tuple[int, str]:
    result = subprocess.run(
        ["git", "-C", str(workspace), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode, (result.stdout + result.stderr).strip()


def main() -> None:
    parser = argparse.ArgumentParser(prog="p5r-agent", description="Safety-first P5R project inspection tools")
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="List files in a workspace")
    scan.add_argument("workspace", type=Path)

    validate = sub.add_parser("validate", help="Validate JSON and basic local HTML links")
    validate.add_argument("workspace", type=Path)

    search = sub.add_parser("search", help="Search text files")
    search.add_argument("workspace", type=Path)
    search.add_argument("query")
    search.add_argument("--ext", action="append", help="Limit to extension, e.g. .js (repeatable)")

    git = sub.add_parser("git", help="Read-only Git inspection")
    git.add_argument("workspace", type=Path)
    git.add_argument("operation", choices=["status", "diff"])

    args = parser.parse_args()
    workspace = args.workspace.expanduser().resolve()

    if args.command == "scan":
        print("\n".join(scan_files(workspace)))
    elif args.command == "validate":
        result = validate_workspace(workspace)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        raise SystemExit(1 if any(result.values()) else 0)
    elif args.command == "search":
        extensions = {item if item.startswith(".") else f".{item}" for item in args.ext} if args.ext else None
        print(json.dumps(search_text(workspace, args.query, extensions), ensure_ascii=False, indent=2))
    elif args.command == "git":
        operation = ["status", "--short"] if args.operation == "status" else ["diff", "--"]
        code, output = _git(workspace, *operation)
        print(output)
        raise SystemExit(code)
