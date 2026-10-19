# P5R project rules

## Website
- Preserve the distinction between Characters, Confidants, Personas, Palaces, and other game entities.
- Keep data-driven content consistent with the existing repository patterns.
- Validate JSON after data changes and check local links after moving pages.
- Prefer accessible, responsive UI and respect reduced-motion preferences.
- Do not overwrite or publish changes without approval.

## 3D and animation
- Inspect the source file and available rig/animation data before modifying an asset.
- Preserve a copy of original assets before any destructive conversion.
- Prefer reproducible Blender scripts and record Blender version and export settings.
- Verify exported models in a viewer/browser; successful export alone does not prove the animation works.
- Do not assume every character model has a usable rig or animation clips.

## GBX
- Identify the source game, file variant, and likely format before choosing tools.
- Do not assume that all files ending in .gbx are interchangeable or convertible.
- Do not run unknown converters or scripts against important files without sandboxing and approval.
- Record the tool/version and conversion limitations.

## Agent behavior
- Separate diagnosis, proposed plan, execution, and validation.
- Report what was actually tested and what remains unverified.
- Ask for approval before writes, deletes, commits, pushes, merges, or deployments.
