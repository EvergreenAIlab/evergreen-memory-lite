"""Non-destructive local runner with dry-run as the default."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from .cards import Card, build_card, render_card
from .dashboard import DASHBOARD_NAME, write_dashboard
from .household import HOUSEHOLD_OUTPUT_NAMES, parse_household_note, render_household_outputs
from .intake import (
    EXTRACTION_REPORT_NAME,
    EXTRACTED_DIR_NAME,
    SKIPPED_FILES_NAME,
    IntakeReport,
    extract_documents,
    render_extraction_report,
    render_skipped_files,
)
from .privacy import classify_text
from .registry import initialize_registry, register_card
from .search import MEMORY_INDEX_NAME, SEARCH_INDEX_NAME, build_search_records, render_memory_index, write_search_index


@dataclass(frozen=True)
class RunResult:
    dry_run: bool
    cards: tuple[Card, ...]
    household_outputs: tuple[Path, ...] = ()
    intake_outputs: tuple[Path, ...] = ()


def run(
    input_dir: Path,
    output_dir: Path = Path("output/cards"),
    *,
    write: bool = False,
    household_admin: bool = False,
    document_intake: bool = False,
) -> RunResult:
    """Plan or explicitly write cards while leaving all source files untouched."""

    input_dir = input_dir.resolve()
    output_dir = output_dir.resolve()
    if not input_dir.is_dir():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")

    card_output_dir = output_dir / "cards" if household_admin else output_dir
    intake_report: IntakeReport | None = extract_documents(input_dir, output_dir) if document_intake else None
    source_texts: list[tuple[Path, str]] = []
    if intake_report is not None:
        source_texts.extend((document.source, document.extracted_markdown) for document in intake_report.extracted)
    else:
        for source in sorted(input_dir.rglob("*.md")):
            text = source.read_text(encoding="utf-8")
            source_texts.append((source, text))

    cards = [
        _build_card_for_input(source, card_output_dir, classify_text(text), text, document_intake=document_intake)
        for source, text in source_texts
    ]

    household_documents: dict[str, str] = {}
    household_paths: tuple[Path, ...] = ()
    search_records = []
    search_index_path: Path | None = None
    if household_admin:
        notes = [parse_household_note(source, text) for source, text in source_texts]
        household_documents = render_household_outputs(notes, cards, output_dir)
        search_records = build_search_records(notes, cards, output_dir)
        household_documents[MEMORY_INDEX_NAME] = render_memory_index(search_records)
        search_index_path = output_dir / SEARCH_INDEX_NAME
        household_paths = tuple(output_dir / name for name in (*HOUSEHOLD_OUTPUT_NAMES, MEMORY_INDEX_NAME)) + (search_index_path,)

    intake_paths: tuple[Path, ...] = ()
    if intake_report is not None:
        intake_paths = tuple(document.extracted_path for document in intake_report.extracted) + (
            output_dir / EXTRACTION_REPORT_NAME,
            output_dir / SKIPPED_FILES_NAME,
            output_dir / DASHBOARD_NAME,
        )

    if not write:
        return RunResult(
            dry_run=True,
            cards=tuple(cards),
            household_outputs=household_paths,
            intake_outputs=intake_paths,
        )

    destinations = [card.destination for card in cards]
    duplicate_destinations = sorted(
        {destination for destination in destinations if destinations.count(destination) > 1}
    )
    if duplicate_destinations:
        joined = ", ".join(str(path) for path in duplicate_destinations)
        raise FileExistsError(f"Multiple sources map to the same card: {joined}")

    existing = [path for path in [*destinations, *household_paths, *intake_paths] if path.exists()]
    if existing:
        joined = ", ".join(str(path) for path in existing)
        raise FileExistsError(f"Refusing to overwrite existing card(s): {joined}")

    card_output_dir.mkdir(parents=True, exist_ok=True)
    local_state_dir = card_output_dir.parent
    registry_path = local_state_dir / "registry.sqlite"
    initialize_registry(registry_path)
    created_at = datetime.now(timezone.utc).isoformat()

    if intake_report is not None:
        extracted_dir = output_dir / EXTRACTED_DIR_NAME
        extracted_dir.mkdir(parents=True, exist_ok=True)
        for document in intake_report.extracted:
            with document.extracted_path.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(document.extracted_markdown)
        with (output_dir / EXTRACTION_REPORT_NAME).open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(render_extraction_report(intake_report))
        with (output_dir / SKIPPED_FILES_NAME).open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(render_skipped_files(intake_report.skipped))

    for card in cards:
        with card.destination.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(render_card(card))
        register_card(registry_path, card, created_at)

    for name, content in household_documents.items():
        with (output_dir / name).open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
    if search_index_path is not None:
        write_search_index(search_index_path, search_records)
    if intake_report is not None:
        write_dashboard(output_dir)

    audit_path = local_state_dir / "audit.jsonl"
    event = {
        "created_at": created_at,
        "event": (
            "document_intake_household_created"
            if document_intake and household_admin
            else "document_intake_created"
            if document_intake
            else "household_admin_created"
            if household_admin
            else "cards_created"
        ),
        "count": len(cards),
    }
    outputs: list[str] = []
    if household_admin:
        outputs.extend([*household_documents, SEARCH_INDEX_NAME])
    if intake_report is not None:
        outputs.extend([EXTRACTION_REPORT_NAME, SKIPPED_FILES_NAME, DASHBOARD_NAME])
    if outputs:
        event["outputs"] = outputs
    with audit_path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(event, sort_keys=True) + "\n")

    return RunResult(
        dry_run=False,
        cards=tuple(cards),
        household_outputs=household_paths,
        intake_outputs=intake_paths,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Directory containing Markdown notes")
    parser.add_argument("--output", type=Path, default=Path("output/cards"), help="Card output directory")
    parser.add_argument("--write", action="store_true", help="Explicitly create local outputs")
    parser.add_argument(
        "--household-admin",
        action="store_true",
        help="Plan or create household admin Markdown outputs and local search memory",
    )
    parser.add_argument(
        "--document-intake",
        action="store_true",
        help="Extract .txt, .md, .docx, and digital .pdf files before generating outputs",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run(
        args.input,
        args.output,
        write=args.write,
        household_admin=args.household_admin,
        document_intake=args.document_intake,
    )
    mode = "DRY RUN" if result.dry_run else "WRITE"
    print(f"{mode}: {len(result.cards)} card(s)")
    for card in result.cards:
        print(f"- {card.source.name} -> {card.destination} [{card.tier.name}]")
    for output in result.household_outputs:
        print(f"- household output -> {output}")
    for output in result.intake_outputs:
        print(f"- intake output -> {output}")
    return 0


def _build_card_for_input(source: Path, output_dir: Path, tier, text: str, *, document_intake: bool) -> Card:
    card = build_card(source, output_dir, tier, text)
    if not document_intake:
        return card
    destination = output_dir / f"{source.name}.card.md"
    return Card(source=card.source, destination=destination, tier=card.tier, digest=card.digest, title=card.title)


if __name__ == "__main__":
    raise SystemExit(main())
