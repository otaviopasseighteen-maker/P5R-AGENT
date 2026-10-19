"""Conservative metadata inspection for files with a .gbx extension.

This module does not decode game assets or attempt conversion. The extension and
header alone are insufficient to guarantee which tools can process a file.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GbxInspection:
    path: str
    size_bytes: int
    extension_matches: bool
    header_hex: str
    header_text: str
    possible_gbx_header: bool
    note: str


def inspect_gbx(path: str | Path) -> GbxInspection:
    """Read only the first 64 bytes and report cautious metadata."""
    file_path = Path(path).expanduser().resolve()
    if not file_path.is_file():
        raise FileNotFoundError(file_path)
    with file_path.open("rb") as handle:
        header = handle.read(64)
    header_text = "".join(chr(byte) if 32 <= byte < 127 else "." for byte in header)
    possible_header = b"GBX" in header[:16].upper()
    return GbxInspection(
        path=str(file_path), size_bytes=file_path.stat().st_size,
        extension_matches=file_path.suffix.lower() == ".gbx",
        header_hex=header.hex(" "), header_text=header_text,
        possible_gbx_header=possible_header,
        note=("Header resembles a GBX marker; identify the source game and format before choosing a parser."
              if possible_header else "No obvious GBX marker found in the first 16 bytes; this does not prove the file is invalid."),
    )
