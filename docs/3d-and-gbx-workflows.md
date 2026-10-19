# Blender, 3D and GBX workflow

## Current status

The first scaffold can detect a Blender executable and inspect the first bytes of a file. It does **not** yet edit Blender projects, create animations, decode GBX assets, or convert game files.

## Blender adapter roadmap

1. Locate Blender through PATH or the BLENDER_EXECUTABLE environment variable.
2. Report the installed version.
3. Add a reviewed, generated Python script for a specific task (inspect scene, list objects, inspect armatures/actions, export GLB).
4. Require explicit approval before executing generated scripts or writing output files.
5. Run output validation and report warnings, logs, and exact output paths.
6. Add browser/viewer checks for exported animations.

Do not execute arbitrary project-provided scripts automatically. Use a dedicated working copy for modifications.

## GBX investigation roadmap

1. Record file extension, size, initial bytes, and likely source game.
2. Identify the specific GBX variant and the tool/library that supports it.
3. Check tool license, platform compatibility, and conversion limitations.
4. Convert only on an approved copy, preserving the source.
5. Validate the converted model/animation in a compatible viewer.

A .gbx suffix is not enough to promise that a file can be opened or converted. Conversion support must be verified for the actual file type and source game.

## Web delivery

When a model can be converted correctly, GLB/glTF is a likely target for web display. The web implementation may use Three.js or another compatible viewer. The browser scene, asset loading, animation playback, and performance should all be tested separately.
