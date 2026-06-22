"""Local SQLite search and source-traceable memory output."""

from __future__ import annotations

import argparse
import sqlite3
import sys
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, Sequence

from .cards import Card
from .household import HouseholdNote, note_risk_messages


MEMORY_INDEX_NAME = "memory_index.md"
SEARCH_INDEX_NAME = "search_index.sqlite"
ITEM_TYPES = ("source", "card", "action", "event", "risk")


@dataclass(frozen=True)
class SearchRecord:
    item_id: str
    item_type: str
    title: str
    text: str
    source_file: str
    output_file: str
    category: str
    owner: str
    status: str
    privacy_tier: str
    date: str
    due_date: str


def build_search_records(notes: Iterable[HouseholdNote], cards: Iterable[Card], output_dir: Path) -> list[SearchRecord]:
    """Build deterministic records from parsed notes without writing anything."""

    cards_by_source = {card.source: card for card in cards}
    records: list[SearchRecord] = []
    for note in sorted(notes, key=lambda item: item.source.name.casefold()):
        common = {
            "source_file": note.source.name,
            "category": note.category,
            "owner": note.owner or "",
            "status": note.status,
            "privacy_tier": note.privacy_tier.name if note.privacy_tier is not None else "Unknown",
            "date": note.date or "",
            "due_date": note.due_date or "",
        }
        records.append(SearchRecord(f"source:{note.source.name}", "source", note.title, note.summary, output_file="source_index.md", **common))
        card = cards_by_source[note.source]
        try:
            card_path = card.destination.relative_to(output_dir).as_posix()
        except ValueError:
            card_path = card.destination.name
        records.append(SearchRecord(f"card:{note.source.name}", "card", note.title, note.summary, output_file=card_path, **common))
        for index, action in enumerate(note.actions, start=1):
            records.append(SearchRecord(f"action:{note.source.name}:{index}", "action", action, f"{action} — {note.summary}", output_file="action_list.md", **common))
        for index, event in enumerate(note.events, start=1):
            event_common = {**common, "date": event.date}
            records.append(SearchRecord(f"event:{note.source.name}:{index}", "event", event.event, event.event, output_file="timeline.md", **event_common))
        for index, risk in enumerate(note_risk_messages(note), start=1):
            records.append(SearchRecord(f"risk:{note.source.name}:{index}", "risk", f"Risk for {note.title}", risk, output_file="risk_flags.md", **common))
    return records


def write_search_index(path: Path, records: Iterable[SearchRecord]) -> None:
    """Create a new local search index; never overwrite an existing file."""

    if path.exists():
        raise FileExistsError(f"Refusing to overwrite search index: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.execute(
            """CREATE TABLE memory_items (
                item_id TEXT PRIMARY KEY, item_type TEXT NOT NULL, title TEXT NOT NULL,
                text TEXT NOT NULL, source_file TEXT NOT NULL, output_file TEXT NOT NULL,
                category TEXT NOT NULL, owner TEXT NOT NULL, status TEXT NOT NULL,
                privacy_tier TEXT NOT NULL, date TEXT NOT NULL, due_date TEXT NOT NULL
            )"""
        )
        columns = tuple(SearchRecord.__dataclass_fields__)
        placeholders = ", ".join("?" for _ in columns)
        connection.executemany(
            f"INSERT INTO memory_items ({', '.join(columns)}) VALUES ({placeholders})",
            ([asdict(record)[column] for column in columns] for record in records),
        )
        connection.execute("CREATE INDEX memory_items_filters ON memory_items (item_type, privacy_tier, date, due_date)")


def query_search_index(
    path: Path,
    *,
    query: str | None = None,
    item_type: str | None = None,
    category: str | None = None,
    owner: str | None = None,
    status: str | None = None,
    privacy_tier: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 20,
) -> list[SearchRecord]:
    """Query the local index with simple substring and exact metadata filters."""

    if not path.is_file():
        raise FileNotFoundError(f"Search index does not exist: {path}")
    if limit < 1:
        raise ValueError("limit must be at least 1")
    clauses: list[str] = []
    parameters: list[object] = []
    if query:
        clauses.append("(title LIKE ? OR text LIKE ?)")
        pattern = f"%{query}%"
        parameters.extend((pattern, pattern))
    for column, value in (("item_type", item_type), ("category", category), ("owner", owner), ("status", status), ("privacy_tier", privacy_tier)):
        if value:
            clauses.append(f"{column} = ? COLLATE NOCASE")
            parameters.append(value)
    relevant_date = "CASE WHEN due_date != '' THEN due_date ELSE date END"
    if date_from:
        clauses.append(f"{relevant_date} >= ?")
        parameters.append(_valid_date(date_from))
    if date_to:
        clauses.append(f"{relevant_date} <= ?")
        parameters.append(_valid_date(date_to))
    sql = "SELECT * FROM memory_items"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += f" ORDER BY {relevant_date}, item_type, source_file, item_id LIMIT ?"
    parameters.append(limit)
    with sqlite3.connect(path) as connection:
        connection.row_factory = sqlite3.Row
        return [SearchRecord(**dict(row)) for row in connection.execute(sql, parameters)]


def render_memory_index(records: Iterable[SearchRecord]) -> str:
    """Render a readable summary of local searchable memory."""

    items = list(records)
    by_type = {item_type: [item for item in items if item.item_type == item_type] for item_type in ITEM_TYPES}
    tiers = sorted({item.privacy_tier for item in by_type["source"]}) or ["None"]
    lines = [
        "# Local Memory Index",
        "",
        f"- Notes processed: **{len(by_type['source'])}**",
        f"- Actions indexed: **{len(by_type['action'])}**",
        f"- Events indexed: **{len(by_type['event'])}**",
        f"- Risks indexed: **{len(by_type['risk'])}**",
        f"- Privacy tiers present: **{', '.join(tiers)}**",
        "- Source files changed: **0**",
        "",
        "## Quick links",
        "",
        "- [Family brief](family_brief.md)",
        "- [Action list](action_list.md)",
        "- [Timeline](timeline.md)",
        "- [Source index](source_index.md)",
        "- [Risk flags](risk_flags.md)",
        "",
        "## Source notes",
        "",
        "| Source | Title | Category | Privacy |",
        "| --- | --- | --- | --- |",
    ]
    lines.extend(f"| `{item.source_file}` | {_md(item.title)} | {_md(item.category)} | {item.privacy_tier} |" for item in by_type["source"])
    lines.extend(["", "## Actions", "", "| Action | Owner | Due | Source |", "| --- | --- | --- | --- |"])
    lines.extend(f"| {_md(item.title)} | {_md(item.owner or 'Unassigned')} | {item.due_date or '—'} | `{item.source_file}` |" for item in by_type["action"])
    lines.extend(["", "## Events", "", "| Date | Event | Source |", "| --- | --- | --- |"])
    lines.extend(f"| {item.date or '—'} | {_md(item.title)} | `{item.source_file}` |" for item in by_type["event"])
    lines.extend([
        "", "## How to search this memory", "",
        "```powershell",
        ".\\.venv\\Scripts\\python.exe -m evergreen_memory_lite.search --memory . --query receipt",
        ".\\.venv\\Scripts\\python.exe -m evergreen_memory_lite.search --memory . --item-type action",
        "```", "",
        "Search is local, literal, and source-traceable. It does not translate or infer meaning.", "",
    ])
    return "\n".join(lines)


def _valid_date(value: str) -> str:
    if len(value) != 10 or value[4] != "-" or value[7] != "-":
        raise ValueError(f"Expected YYYY-MM-DD, got {value!r}")
    date.fromisoformat(value)
    return value


def _md(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--memory", type=Path, required=True, help="Household admin output directory")
    parser.add_argument("--query", help="Literal substring to find in titles and text")
    parser.add_argument("--item-type", choices=ITEM_TYPES)
    parser.add_argument("--category")
    parser.add_argument("--owner")
    parser.add_argument("--status")
    parser.add_argument("--privacy-tier")
    parser.add_argument("--date-from")
    parser.add_argument("--date-to")
    parser.add_argument("--limit", type=_positive_int, default=20)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = build_parser().parse_args(argv)
    try:
        results = query_search_index(
            args.memory.resolve() / SEARCH_INDEX_NAME,
            query=args.query, item_type=args.item_type, category=args.category,
            owner=args.owner, status=args.status, privacy_tier=args.privacy_tier,
            date_from=args.date_from, date_to=args.date_to, limit=args.limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc
    print(f"{len(results)} result(s)")
    for index, result in enumerate(results, start=1):
        display_date = result.due_date or result.date or "—"
        print(f"\n[{index}] {result.item_type.upper()} — {result.title}")
        print(f"  Source: {result.source_file}")
        print(f"  Output: {result.output_file or '—'}")
        print(f"  Date: {display_date}")
        print(f"  Privacy: {result.privacy_tier}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
