from __future__ import annotations

from pathlib import Path

import pytest

from evergreen_memory_lite.dashboard import DASHBOARD_NAME, render_dashboard, write_dashboard
from evergreen_memory_lite.launcher import collision_safe_destination


def test_dashboard_lists_expected_outputs(tmp_path: Path) -> None:
    output = tmp_path / "output" / "latest"
    output.mkdir(parents=True)
    for name in [
        "extraction_report.md",
        "skipped_files.md",
        "family_brief.md",
        "action_list.md",
        "timeline.md",
        "source_index.md",
        "risk_flags.md",
        "memory_index.md",
    ]:
        (output / name).write_text("demo", encoding="utf-8")
    extracted_dir = output / "extracted"
    extracted_dir.mkdir()
    (extracted_dir / "sample.extracted.md").write_text("demo", encoding="utf-8")

    html = render_dashboard(output)

    assert "Evergreen Memory Lite Dashboard" in html
    assert "extraction_report.md" in html
    assert "sample.extracted.md" in html


def test_write_dashboard_creates_file_and_refuses_overwrite(tmp_path: Path) -> None:
    output = tmp_path / "output" / "latest"
    output.mkdir(parents=True)

    path = write_dashboard(output)

    assert path.name == DASHBOARD_NAME
    assert path.is_file()

    with pytest.raises(FileExistsError):
        write_dashboard(output)


def test_launcher_import_does_not_start_gui() -> None:
    import evergreen_memory_lite.launcher as launcher

    assert launcher.main.__name__ == "main"


def test_collision_safe_destination_avoids_overwrites(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    existing = inbox / "sample.txt"
    existing.write_text("keep", encoding="utf-8")
    other = tmp_path / "sample.txt"
    other.write_text("new", encoding="utf-8")
    monkeypatch.setattr("evergreen_memory_lite.launcher.INBOX", inbox)

    destination = collision_safe_destination(other)

    assert destination.name == "sample_2.txt"
