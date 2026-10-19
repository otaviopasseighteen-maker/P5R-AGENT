"""Command-line entry point for the initial P5R agent foundation."""
import argparse
import json
import subprocess
from dataclasses import asdict
from pathlib import Path

from .blender import inspect_blender
from .gbx import inspect_gbx
from .validator import validate_workspace
from .workspace import scan_files, search_text


def _git(workspace: Path, *args: str) -> tuple[int, str]:
    result = subprocess.run(
        ["git", "-C", str(workspace), *args],
        capture_output=True, text=True, check=False,
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

    blender = sub.add_parser("blender", help="Inspect Blender availability; does not execute scripts")
    blender.add_argument("--executable", help="Optional explicit Blender executable path")

    gbx = sub.add_parser("inspect-gbx", help="Inspect basic metadata of a GBX file without conversion")
    gbx.add_argument("file", type=Path)

    args = parser.parse_args()

    if args.command == "scan":
        print("\n".join(scan_files(args.workspace.expanduser().resolve())))
    elif args.command == "validate":
        result = validate_workspace(args.workspace.expanduser().resolve())
        print(json.dumps(result, ensure_ascii=False, indent=2))
        raise SystemExit(1 if any(result.values()) else 0)
    elif args.command == "search":
        extensions = {item if item.startswith(".") else f".{item}" for item in args.ext} if args.ext else None
        print(json.dumps(search_text(args.workspace.expanduser().resolve(), args.query, extensions), ensure_ascii=False, indent=2))
    elif args.command == "git":
        workspace = args.workspace.expanduser().resolve()
        operation = ["status", "--short"] if args.operation == "status" else ["diff", "--"]
        code, output = _git(workspace, *operation)
        print(output)
        raise SystemExit(code)
    elif args.command == "blender":
        result = inspect_blender(args.executable)
        print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
        raise SystemExit(0 if result.available else 1)
    elif args.command == "inspect-gbx":
        print(json.dumps(asdict(inspect_gbx(args.file)), ensure_ascii=False, indent=2))
