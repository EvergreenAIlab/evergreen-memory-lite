"""Non-destructive local runner with dry-run as the default."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from .cards import Card, build_card, render_card
from .privacy import classify_text
from .registry import initialize_registry, register_card


@dataclass(frozen=True)
class RunResult:
    dry_run: bool
    cards: tuple[Card, ...]


def run(input_dir: Path, output_dir: Path = Path("output/cards"), *, write: bool = False) -> RunResult:
    """Plan or explicitly write cards while leaving all source files untouched."""

    input_dir = input_dir.resolve()
    output_dir = output_dir.resolve()
    if not input_dir.is_dir():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")

    cards: list[Card] = []
    for source in sorted(input_dir.rglob("*.md")):
        text = source.read_text(encoding="utf-8")
        cards.append(build_card(source, output_dir, classify_text(text), text))

    if not write:
        return RunResult(dry_run=True, cards=tuple(cards))

    destinations = [card.destination for card in cards]
    duplicate_destinations = sorted(
        {destination for destination in destinations if destinations.count(destination) > 1}
    )
    if duplicate_destinations:
        joined = ", ".join(str(path) for path in duplicate_destinations)
        raise FileExistsError(f"Multiple sources map to the same card: {joined}")

    existing = [card.destination for card in cards if card.destination.exists()]
    if existing:
        joined = ", ".join(str(path) for path in existing)
        raise FileExistsError(f"Refusing to overwrite existing card(s): {joined}")

    output_dir.mkdir(parents=True, exist_ok=True)
    registry_path = output_dir.parent / "registry.sqlite"
    initialize_registry(registry_path)
    created_at = datetime.now(timezone.utc).isoformat()

    for card in cards:
        with card.destination.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(render_card(card))
        register_card(registry_path, card, created_at)

    audit_path = output_dir.parent / "audit.jsonl"
    event = {"created_at": created_at, "event": "cards_created", "count": len(cards)}
    with audit_path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(event, sort_keys=True) + "\n")

    return RunResult(dry_run=False, cards=tuple(cards))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Directory containing Markdown notes")
    parser.add_argument("--output", type=Path, default=Path("output/cards"), help="Card output directory")
    parser.add_argument("--write", action="store_true", help="Explicitly create local outputs")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run(args.input, args.output, write=args.write)
    mode = "DRY RUN" if result.dry_run else "WRITE"
    print(f"{mode}: {len(result.cards)} card(s)")
    for card in result.cards:
        print(f"- {card.source.name} -> {card.destination} [{card.tier.name}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
