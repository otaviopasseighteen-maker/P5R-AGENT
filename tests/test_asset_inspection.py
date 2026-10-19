from pathlib import Path

from p5r_agent.gbx import inspect_gbx


def test_inspect_gbx_reports_header_without_conversion(tmp_path: Path) -> None:
    asset = tmp_path / "sample.gbx"
    asset.write_bytes(b"GBX DEMO HEADER\x00\x01payload")

    result = inspect_gbx(asset)

    assert result.extension_matches is True
    assert result.size_bytes == len(b"GBX DEMO HEADER\x00\x01payload")
    assert result.possible_gbx_header is True
    assert "before choosing a parser" in result.note


def test_inspect_gbx_rejects_missing_file(tmp_path: Path) -> None:
    try:
        inspect_gbx(tmp_path / "missing.gbx")
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("Expected missing file to raise FileNotFoundError")
