"""Create deterministic Markdown cards without changing source notes."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from .privacy import PrivacyTier


@dataclass(frozen=True)
class Card:
    source: Path
    destination: Path
    tier: PrivacyTier
    digest: str
    title: str


def build_card(source: Path, output_dir: Path, tier: PrivacyTier, text: str) -> Card:
    """Build card metadata from text without writing to disk."""

    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    title = _title_from_text(text) or source.stem
    destination = output_dir / f"{source.stem}.card.md"
    return Card(source=source, destination=destination, tier=tier, digest=digest, title=title)


def _title_from_text(text: str) -> str | None:
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for line in lines[1:]:
            if line.strip() == "---":
                break
            key, separator, value = line.partition(":")
            if separator and key.strip() == "title" and value.strip():
                return value.strip()
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return next((line.lstrip("# ").strip() for line in lines if line.strip()), None)


def render_card(card: Card) -> str:
    """Render a public-safe card containing metadata rather than source content."""

    return (
        f"# {card.title}\n\n"
        f"- Privacy tier: {card.tier.name}\n"
        f"- Source file: {card.source.name}\n"
        f"- SHA-256: `{card.digest}`\n"
    )
