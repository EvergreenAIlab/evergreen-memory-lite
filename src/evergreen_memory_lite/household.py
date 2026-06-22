"""Rule-based household admin parsing and useful Markdown outputs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

from .cards import Card
from .privacy import PrivacyTier


HOUSEHOLD_OUTPUT_NAMES = (
    "family_brief.md",
    "action_list.md",
    "timeline.md",
    "source_index.md",
    "risk_flags.md",
)

_ALLOWED_FIELDS = {
    "privacy_tier",
    "synthetic",
    "category",
    "title",
    "date",
    "due_date",
    "owner",
    "status",
}

_SECTION_ALIASES = {
    "actions": frozenset(
        alias.casefold()
        for alias in ("Actions", "Action items", "Tasks", "待办", "行动", "Oppgaver", "Gjøremål")
    ),
    "events": frozenset(
        alias.casefold()
        for alias in ("Events", "Timeline", "Key dates", "事件", "时间线", "Hendelser", "Tidslinje")
    ),
    "risks": frozenset(
        alias.casefold()
        for alias in ("Risks", "Risk flags", "Warnings", "风险", "风险提示", "Risiko", "Varsler")
    ),
}


@dataclass(frozen=True)
class TimelineEvent:
    date: str
    event: str


@dataclass(frozen=True)
class HouseholdNote:
    source: Path
    title: str
    category: str
    privacy_tier: PrivacyTier | None
    synthetic: bool
    date: str | None
    due_date: str | None
    owner: str | None
    status: str
    summary: str
    actions: tuple[str, ...]
    events: tuple[TimelineEvent, ...]
    risks: tuple[str, ...]
    issues: tuple[str, ...]


def parse_household_note(source: Path, text: str) -> HouseholdNote:
    """Parse a small strict frontmatter block and three optional list sections."""

    metadata, content_lines, issues = _parse_frontmatter(text)
    body_lines, actions, events, risks, section_issues = _parse_sections(content_lines)
    issues.extend(section_issues)

    raw_tier = metadata.get("privacy_tier", "")
    privacy_tier: PrivacyTier | None = None
    if raw_tier:
        try:
            privacy_tier = PrivacyTier.from_label(raw_tier)
        except ValueError:
            issues.append(f"Unsupported privacy_tier value: {raw_tier!r}.")
    else:
        issues.append("Missing privacy_tier; the note cannot be treated as safe input.")

    synthetic = metadata.get("synthetic", "").casefold() == "true"
    if not synthetic:
        issues.append("The synthetic marker is missing or is not true.")

    title = metadata.get("title") or _markdown_title(content_lines) or source.stem
    if "title" not in metadata:
        issues.append("Missing title; a fallback title was used.")

    category = metadata.get("category") or "uncategorized"
    if "category" not in metadata:
        issues.append("Missing category; uncategorized was used.")

    owner = metadata.get("owner") or None
    status = metadata.get("status") or "unspecified"
    if actions and owner is None:
        issues.append("Action owner is missing.")
    if actions and "due_date" not in metadata:
        issues.append("Action due_date is missing.")
    if actions and "status" not in metadata:
        issues.append("Action status is missing.")

    note_date = _validated_date(metadata.get("date"), "date", issues)
    due_date = _validated_date(metadata.get("due_date"), "due_date", issues)
    summary = _summary(body_lines, title)

    return HouseholdNote(
        source=source,
        title=title,
        category=category,
        privacy_tier=privacy_tier,
        synthetic=synthetic,
        date=note_date,
        due_date=due_date,
        owner=owner,
        status=status,
        summary=summary,
        actions=tuple(actions),
        events=tuple(events),
        risks=tuple(risks),
        issues=tuple(issues),
    )


def render_household_outputs(
    notes: Iterable[HouseholdNote], cards: Iterable[Card], output_dir: Path
) -> dict[str, str]:
    """Render the five household admin outputs without writing any files."""

    note_list = sorted(notes, key=lambda note: note.source.name.casefold())
    card_by_source = {card.source: card for card in cards}
    documents = {
        "family_brief.md": _render_family_brief(note_list),
        "action_list.md": _render_action_list(note_list),
        "timeline.md": _render_timeline(note_list),
        "source_index.md": _render_source_index(note_list, card_by_source, output_dir),
        "risk_flags.md": _render_risk_flags(note_list),
    }
    return documents


def _parse_frontmatter(text: str) -> tuple[dict[str, str], list[str], list[str]]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, lines, ["Missing frontmatter; structured fields are unavailable."]

    try:
        closing_index = next(index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration as exc:
        raise ValueError("Frontmatter is missing its closing '---' delimiter.") from exc

    metadata: dict[str, str] = {}
    for line_number, line in enumerate(lines[1:closing_index], start=2):
        if not line.strip():
            continue
        key, separator, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if not separator or not key or not value:
            raise ValueError(f"Invalid frontmatter line {line_number}: {line!r}")
        if key not in _ALLOWED_FIELDS:
            raise ValueError(f"Unsupported frontmatter field on line {line_number}: {key!r}")
        if key in metadata:
            raise ValueError(f"Duplicate frontmatter field on line {line_number}: {key!r}")
        metadata[key] = value
    return metadata, lines[closing_index + 1 :], []


def _parse_sections(
    lines: list[str],
) -> tuple[list[str], list[str], list[TimelineEvent], list[str], list[str]]:
    body: list[str] = []
    actions: list[str] = []
    events: list[TimelineEvent] = []
    risks: list[str] = []
    issues: list[str] = []
    section: str | None = None

    for line in lines:
        stripped = line.strip()
        matched_section = _section_name(stripped)
        if matched_section is not None:
            section = matched_section
            continue
        if section is None:
            body.append(line)
            continue
        if not stripped:
            continue
        if not stripped.startswith("- "):
            issues.append(f"Ignored malformed {section} entry: {stripped!r}.")
            continue
        item = stripped[2:].strip()
        if section == "actions":
            actions.append(item)
        elif section == "risks":
            risks.append(item)
        else:
            event_date, separator, event_text = item.partition(":")
            if not separator or not event_text.strip() or not _is_iso_date(event_date.strip()):
                issues.append(f"Ignored malformed event entry: {item!r}.")
                continue
            events.append(TimelineEvent(date=event_date.strip(), event=event_text.strip()))
    return body, actions, events, risks, issues


def _section_name(heading: str) -> str | None:
    normalized = heading.lstrip("#").strip().rstrip(":：").strip().casefold()
    for section, aliases in _SECTION_ALIASES.items():
        if normalized in aliases:
            return section
    return None


def _validated_date(value: str | None, field: str, issues: list[str]) -> str | None:
    if value is None:
        return None
    if not _is_iso_date(value):
        issues.append(f"Invalid {field} value {value!r}; expected YYYY-MM-DD.")
        return None
    return value


def _is_iso_date(value: str) -> bool:
    if len(value) != 10 or value[4] != "-" or value[7] != "-":
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _markdown_title(lines: list[str]) -> str | None:
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return None


def _summary(lines: list[str], fallback: str) -> str:
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped
    return fallback


def _risk_entries(notes: list[HouseholdNote]) -> list[str]:
    entries: list[str] = []
    for note in notes:
        source = f"`{note.source.name}`"
        if note.privacy_tier is None:
            entries.append(f"{source}: privacy tier is unknown; do not treat this note as safe input.")
        elif note.privacy_tier is not PrivacyTier.P0:
            entries.append(
                f"{source}: {note.privacy_tier.name} is not supported as safe input; use synthetic P0 notes only."
            )
        if not note.synthetic:
            entries.append(f"{source}: synthetic marker is not confirmed.")
        entries.extend(f"{source}: {issue}" for issue in note.issues)
        entries.extend(f"{source}: {risk}" for risk in note.risks)
    return entries


def _render_family_brief(notes: list[HouseholdNote]) -> str:
    risk_entries = _risk_entries(notes)
    non_p0_count = sum(note.privacy_tier is not PrivacyTier.P0 for note in notes)
    lines = [
        "# Family / Small-Office Brief",
        "",
        f"- Notes processed: **{len(notes)}**",
        "- Source files changed: **0**",
        f"- Risk flags: **{len(risk_entries)}** ({non_p0_count} non-P0 or unknown note(s))",
        "",
        "## Key things to know",
        "",
    ]
    lines.extend(f"- **{_escape(note.title)}** ({_escape(note.category)}): {_escape(note.summary)}" for note in notes)
    if not notes:
        lines.append("- No notes were found.")

    upcoming: list[tuple[str, str]] = []
    for note in notes:
        if note.due_date:
            for action in note.actions:
                upcoming.append((note.due_date, f"{action} — `{note.source.name}`"))
        for event in note.events:
            upcoming.append((event.date, f"{event.event} — `{note.source.name}`"))
    lines.extend(["", "## Upcoming items", ""])
    if upcoming:
        lines.extend(f"- **{item_date}** — {_escape(item)}" for item_date, item in sorted(upcoming))
    else:
        lines.append("- No dated actions or events were found.")
    lines.extend(
        [
            "",
            "## Risk summary",
            "",
            f"See [risk_flags.md](risk_flags.md) for {len(risk_entries)} flag(s) and the privacy reminder.",
            "",
        ]
    )
    return "\n".join(lines)


def _render_action_list(notes: list[HouseholdNote]) -> str:
    lines = [
        "# Action List",
        "",
        "| Task | Owner | Due date | Source note | Status | Reason / context |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    action_count = 0
    for note in sorted(notes, key=lambda item: (item.due_date or "9999-99-99", item.source.name)):
        for action in note.actions:
            action_count += 1
            lines.append(
                "| "
                + " | ".join(
                    [
                        _escape(action),
                        _escape(note.owner or "Unassigned"),
                        note.due_date or "Not provided",
                        f"`{note.source.name}`",
                        _escape(note.status),
                        _escape(note.summary),
                    ]
                )
                + " |"
            )
    if action_count == 0:
        lines.append("| No actions found | — | — | — | — | — |")
    lines.extend(["", "Source files changed: **0**", ""])
    return "\n".join(lines)


def _render_timeline(notes: list[HouseholdNote]) -> str:
    rows: list[tuple[str, str, str, str]] = []
    for note in notes:
        related_action = note.actions[0] if note.actions else "—"
        for event in note.events:
            rows.append((event.date, event.event, note.source.name, related_action))
    lines = [
        "# Timeline",
        "",
        "| Date | Event | Source note | Related action |",
        "| --- | --- | --- | --- |",
    ]
    if rows:
        for event_date, event, source, action in sorted(rows):
            lines.append(
                f"| {event_date} | {_escape(event)} | `{source}` | {_escape(action)} |"
            )
    else:
        lines.append("| — | No events found | — | — |")
    lines.extend(["", "Source files changed: **0**", ""])
    return "\n".join(lines)


def _render_source_index(
    notes: list[HouseholdNote], card_by_source: dict[Path, Card], output_dir: Path
) -> str:
    lines = [
        "# Source Index",
        "",
        "| Source file | Title | Category | Privacy tier | Generated card | Referenced by |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for note in notes:
        outputs = ["family_brief.md", "source_index.md", "risk_flags.md"]
        if note.actions:
            outputs.append("action_list.md")
        if note.events:
            outputs.append("timeline.md")
        card = card_by_source[note.source]
        try:
            card_path = card.destination.relative_to(output_dir).as_posix()
        except ValueError:
            card_path = card.destination.name
        tier = note.privacy_tier.name if note.privacy_tier is not None else "Unknown"
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{note.source.name}`",
                    _escape(note.title),
                    _escape(note.category),
                    tier,
                    f"`{card_path}`",
                    ", ".join(f"`{name}`" for name in outputs),
                ]
            )
            + " |"
        )
    if not notes:
        lines.append("| — | No sources found | — | — | — | — |")
    lines.extend(["", "Source files changed: **0**", ""])
    return "\n".join(lines)


def _render_risk_flags(notes: list[HouseholdNote]) -> str:
    entries = _risk_entries(notes)
    lines = [
        "# Risk Flags",
        "",
        "- Source files changed: **0**",
        "- Privacy boundary: real sensitive data is not supported. Use deliberately synthetic P0 notes only.",
        "",
        "## Flags",
        "",
    ]
    if entries:
        lines.extend(f"- {entry}" for entry in entries)
    else:
        lines.append("- No structural or privacy flags were found.")
    lines.append("")
    return "\n".join(lines)


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()
