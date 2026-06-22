import hashlib
from pathlib import Path

import pytest

from evergreen_memory_lite.household import HOUSEHOLD_OUTPUT_NAMES, parse_household_note
from evergreen_memory_lite.runner import main, run
from evergreen_memory_lite.search import MEMORY_INDEX_NAME, SEARCH_INDEX_NAME


ROOT = Path(__file__).resolve().parents[1]


def structured_note(*, tier: str = "P0") -> str:
    return f"""---
privacy_tier: {tier}
synthetic: true
category: household task
title: Prepare fictional supply checklist
date: 2026-06-22
due_date: 2026-07-03
owner: Alex Example
status: planned
---

Prepare an invented checklist for the imaginary Cedar Room.

Actions:
- Add two demo towels to the checklist

Events:
- 2026-07-03: Review the fictional supply checklist

Risks:
- Keep every checklist detail fictional
"""


def file_hashes(directory: Path) -> dict[Path, str]:
    return {
        path.relative_to(directory): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in directory.rglob("*")
        if path.is_file()
    }


def test_household_admin_dry_run_writes_nothing(tmp_path: Path) -> None:
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    (inbox / "note.md").write_text(structured_note(), encoding="utf-8")
    before = file_hashes(inbox)
    output = tmp_path / "output" / "household_admin"

    result = run(inbox, output, household_admin=True)

    assert result.dry_run is True
    assert {path.name for path in result.household_outputs} == {
        *HOUSEHOLD_OUTPUT_NAMES,
        MEMORY_INDEX_NAME,
        SEARCH_INDEX_NAME,
    }
    assert not output.exists()
    assert file_hashes(inbox) == before


def test_household_admin_cli_creates_readable_outputs_without_source_changes(tmp_path: Path) -> None:
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    (inbox / "note.md").write_text(structured_note(), encoding="utf-8")
    before = file_hashes(inbox)
    output = tmp_path / "output" / "household_admin"

    assert main(["--input", str(inbox), "--output", str(output), "--household-admin", "--write"]) == 0

    assert {path.name for path in output.glob("*.md")} == {*HOUSEHOLD_OUTPUT_NAMES, MEMORY_INDEX_NAME}
    assert (output / "cards" / "note.card.md").is_file()
    assert (output / "registry.sqlite").is_file()
    assert (output / "audit.jsonl").is_file()
    assert (output / SEARCH_INDEX_NAME).is_file()
    assert file_hashes(inbox) == before
    assert all(path.is_relative_to(output) for path in output.rglob("*") if path.is_file())

    for name in HOUSEHOLD_OUTPUT_NAMES:
        text = (output / name).read_text(encoding="utf-8")
        assert text.startswith("# ")
        assert "`note.md`" in text
    assert "Add two demo towels" in (output / "action_list.md").read_text(encoding="utf-8")
    assert "2026-07-03" in (output / "timeline.md").read_text(encoding="utf-8")
    assert "cards/note.card.md" in (output / "source_index.md").read_text(encoding="utf-8")
    assert "Source files changed: **0**" in (output / "family_brief.md").read_text(encoding="utf-8")
    assert "# Local Memory Index" in (output / MEMORY_INDEX_NAME).read_text(encoding="utf-8")


def test_non_p0_note_is_flagged_as_unsupported(tmp_path: Path) -> None:
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    (inbox / "fictional_private_note.md").write_text(structured_note(tier="P2"), encoding="utf-8")
    output = tmp_path / "output" / "household_admin"

    run(inbox, output, write=True, household_admin=True)

    risks = (output / "risk_flags.md").read_text(encoding="utf-8")
    assert "`fictional_private_note.md`" in risks
    assert "P2 is not supported as safe input" in risks
    assert "1 non-P0 or unknown note(s)" in (output / "family_brief.md").read_text(encoding="utf-8")


def test_missing_action_fields_are_reported_gently(tmp_path: Path) -> None:
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    text = structured_note().replace("due_date: 2026-07-03\n", "").replace("owner: Alex Example\n", "")
    (inbox / "note.md").write_text(text, encoding="utf-8")
    output = tmp_path / "output" / "household_admin"

    run(inbox, output, write=True, household_admin=True)

    risks = (output / "risk_flags.md").read_text(encoding="utf-8")
    assert "Action owner is missing" in risks
    assert "Action due_date is missing" in risks


def test_household_admin_refuses_to_overwrite_existing_report(tmp_path: Path) -> None:
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    (inbox / "note.md").write_text(structured_note(), encoding="utf-8")
    before = file_hashes(inbox)
    output = tmp_path / "output" / "household_admin"
    output.mkdir(parents=True)
    existing = output / "family_brief.md"
    existing.write_text("keep me", encoding="utf-8")

    with pytest.raises(FileExistsError):
        run(inbox, output, write=True, household_admin=True)

    assert existing.read_text(encoding="utf-8") == "keep me"
    assert not (output / "cards").exists()
    assert file_hashes(inbox) == before


def test_strict_frontmatter_rejects_unknown_fields(tmp_path: Path) -> None:
    source = tmp_path / "note.md"
    text = structured_note().replace("category: household task", "unexpected: value")

    with pytest.raises(ValueError, match="Unsupported frontmatter field"):
        parse_household_note(source, text)


def test_section_aliases_accept_simple_markdown_headings(tmp_path: Path) -> None:
    source = tmp_path / "note.md"
    text = (
        structured_note()
        .replace("Actions:", "## GJØREMÅL:")
        .replace("Events:", "## TIDSLINJE:")
        .replace("Risks:", "## VARSLER:")
    )

    note = parse_household_note(source, text)

    assert note.actions == ("Add two demo towels to the checklist",)
    assert note.events[0].event == "Review the fictional supply checklist"
    assert note.risks == ("Keep every checklist detail fictional",)


def test_multilingual_samples_preserve_utf8_and_section_aliases(tmp_path: Path) -> None:
    inbox = ROOT / "data" / "synthetic"
    before = file_hashes(inbox)
    output = tmp_path / "output" / "household_admin"

    run(inbox, output, write=True, household_admin=True)

    actions = (output / "action_list.md").read_text(encoding="utf-8")
    timeline = (output / "timeline.md").read_text(encoding="utf-8")
    risks = (output / "risk_flags.md").read_text(encoding="utf-8")

    assert "Confirm the fictional museum opening time" in actions
    assert "给每个演示收纳箱添加虚构类别标签" in actions
    assert "Arkiver eksempelkvitteringen sammen med husholdningens demofiler" in actions
    assert "检查演示收纳箱标签" in timeline
    assert "Kontroller arkiveringen av eksempelkvitteringen" in timeline
    assert "所有房间和收纳信息均为虚构内容" in risks
    assert "Butikken, beløpet og referansen er oppdiktet" in risks
    assert file_hashes(inbox) == before
