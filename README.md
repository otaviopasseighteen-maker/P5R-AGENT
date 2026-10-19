# P5R Developer Agent

A safety-first developer agent for the Persona 5 Royal website, with planned specialist workflows for web development, Blender/3D animation, and investigation of `.gbx` assets.

## Status

**Early prototype.** The local web panel and optional AI chat are available on `feature/web-panel-local-executor`. This branch adds the first bounded change-proposal engine, but it is not yet wired into the web panel or AI chat. It is not yet a fully autonomous coding agent and has not been validated against the user's local Blender installation or real `.gbx` files.

## Initial capabilities

- Inspect a project workspace without changing files.
- Search text files and list project files through the CLI.
- Validate JSON files and basic local HTML links.
- Show Git status and diffs.
- Detect Blender and inspect basic GBX metadata.
- Local-only web control panel with chat via the OpenAI API, when configured.
- Experimental Python API for proposing bounded text-file edits, requiring explicit approval before applying.

## Local panel setup

Requires Python 3.11+ and a local project directory. From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
$env:P5R_AGENT_WORKSPACE = "C:\\caminho\\para\\Persona-5-Royal"
# Optional: enables AI chat through the OpenAI API; API usage may incur charges.
$env:OPENAI_API_KEY = "sua-chave-de-api"
p5r-agent-panel
```

Then open **http://127.0.0.1:8765** in your browser. On macOS/Linux, activate with `source .venv/bin/activate` and set environment variables using `export NAME=value`.

The panel listens on localhost only. Keep it on your own computer; do not port-forward or expose it to the internet. The OpenAI API key is read from the environment and is never sent to the browser. A ChatGPT subscription does not automatically include OpenAI API credits.

## Panel actions

- Chat with the configured AI model for guidance and planning.
- Scan files, validate JSON/relative HTML links, and inspect Git status.
- Check whether Blender is available.
- Inspect the header and metadata of a selected GBX file.

This version's web panel does **not** yet expose file changes. It does not run arbitrary shell commands or Blender scripts, convert GBX assets, commit, push, merge, or deploy. AI chat is advisory; it is not yet connected to tool execution.

## Experimental change proposal API

`p5r_agent.proposals` provides a foundation for a future review-and-apply UI:

- Proposes edits only to existing, bounded UTF-8 text files with an allowlisted extension.
- Refuses common secret files such as `.env`.
- Stores proposals and backups outside the target workspace under `~/.p5r-agent/state` by default.
- Does not change the workspace when a proposal is created.
- Requires an explicit `approved=True` argument to apply a pending proposal.
- Checks the original file's SHA-256 before applying; if the file changed after review, it refuses to overwrite it.
- Creates a backup before replacing a file and uses an atomic replacement for the write.
- Supports rejecting pending proposals.

This module is an experimental library API only in this branch. The browser UI does not call it yet. Do not expose it to the network or connect model output directly to the approval argument. The next milestone is to add a review screen with a diff, proposal-specific approval, tests, and clear failure reporting.

## Safety model

- Read-only inspection and validation are allowed by default.
- A proposal is not an approval; file changes require a separate explicit approval action.
- No automatic push, merge, or deployment is implemented.
- Treat project files and model metadata as untrusted input.
- Never execute arbitrary commands or Blender scripts without a controlled runner and explicit authorization.

## GBX and Blender notes

Blender automation is feasible when Blender is installed in an accessible environment. A `.gbx` extension alone is not enough to determine the exact game, version, or supported conversion path. Identify the format and available tooling before attempting conversion. GLB/glTF can be useful for web delivery if the source asset can be converted correctly.

## Development

```bash
pytest
```

See `rules/p5r.md` for project-specific constraints.
