from pathlib import Path

import pytest

from evergreen_memory_lite.runner import run


def snapshot(directory: Path) -> dict[Path, bytes]:
    return {path.relative_to(directory): path.read_bytes() for path in directory.rglob("*") if path.is_file()}


def test_runner_defaults_to_dry_run_without_source_mutation(tmp_path: Path) -> None:
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    source = inbox / "note.md"
    source.write_text("# Synthetic note\n\nPrivacy: P0\n", encoding="utf-8")
    before = snapshot(inbox)
    output = tmp_path / "output" / "cards"

    result = run(inbox, output)

    assert result.dry_run is True
    assert len(result.cards) == 1
    assert snapshot(inbox) == before
    assert not output.exists()


def test_explicit_write_creates_outputs_without_source_mutation(tmp_path: Path) -> None:
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    (inbox / "note.md").write_text("# Synthetic note\n\nPrivacy: P0\n", encoding="utf-8")
    before = snapshot(inbox)
    output = tmp_path / "output" / "cards"

    result = run(inbox, output, write=True)

    assert result.dry_run is False
    assert (output / "note.card.md").is_file()
    assert (output.parent / "registry.sqlite").is_file()
    assert (output.parent / "audit.jsonl").is_file()
    assert snapshot(inbox) == before


def test_runner_refuses_to_overwrite_card(tmp_path: Path) -> None:
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    (inbox / "note.md").write_text("Privacy: P0\n", encoding="utf-8")
    output = tmp_path / "output" / "cards"
    output.mkdir(parents=True)
    existing = output / "note.card.md"
    existing.write_text("keep me", encoding="utf-8")

    with pytest.raises(FileExistsError):
        run(inbox, output, write=True)

    assert existing.read_text(encoding="utf-8") == "keep me"


def test_runner_rejects_duplicate_card_names_before_writing(tmp_path: Path) -> None:
    inbox = tmp_path / "inbox"
    (inbox / "one").mkdir(parents=True)
    (inbox / "two").mkdir()
    (inbox / "one" / "note.md").write_text("Privacy: P0\n", encoding="utf-8")
    (inbox / "two" / "note.md").write_text("Privacy: P0\n", encoding="utf-8")
    output = tmp_path / "output" / "cards"

    with pytest.raises(FileExistsError):
        run(inbox, output, write=True)

    assert not output.exists()
