# P5R Developer Agent

A safety-first developer agent for the Persona 5 Royal website, with planned specialist workflows for web development, Blender/3D animation, and investigation of `.gbx` assets.

## Status

**Foundation scaffold — early development.** This repository is not yet an autonomous agent and has not been validated against the user's local Blender installation or real `.gbx` files.

## Initial capabilities

- Inspect a project workspace without changing files.
- Search text files and list project files.
- Validate JSON files and basic local HTML links.
- Show Git status and diffs.
- Enforce workspace boundaries and approval gates for mutations.
- Keep future integrations modular: web, Blender, GBX research/conversion, and QA.

## Safety model

- Read-only inspection and validation are allowed by default.
- File writes, deletion, commits, and external changes require explicit approval in the calling application.
- No automatic push, merge, or deployment is implemented.
- Treat project files and model metadata as untrusted input.
- Never execute arbitrary commands or Blender scripts without a controlled runner and explicit authorization.

## Quick start

Requires Python 3.11+.

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -e ".[dev]"
p5r-agent --help
p5r-agent scan /path/to/Persona-5-Royal
p5r-agent validate /path/to/Persona-5-Royal
```

## Roadmap

1. Safe workspace scanner, policy, validators, CLI and tests.
2. Task planner and structured approval workflow.
3. Blender adapter using the locally installed Blender executable and Python scripts.
4. GBX format identification and compatible-tool discovery; conversion only where supported.
5. Browser-based QA for the website and exported 3D scenes.
6. Optional GitHub branch/PR workflow after validation.

## Blender and GBX notes

Blender automation is feasible when Blender is installed in an accessible environment. A `.gbx` extension alone is not enough to determine the exact game, version, or supported conversion path. The agent must identify the format and available tooling before attempting conversion. GLB/glTF can be a useful web delivery format when the source asset can be converted correctly.

## Development

```bash
pytest
```

See `rules/p5r.md` for project-specific constraints.
