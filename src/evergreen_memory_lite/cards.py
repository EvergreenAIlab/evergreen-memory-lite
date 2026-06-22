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
    title = next((line.lstrip("# ").strip() for line in text.splitlines() if line.strip()), source.stem)
    destination = output_dir / f"{source.stem}.card.md"
    return Card(source=source, destination=destination, tier=tier, digest=digest, title=title)


def render_card(card: Card) -> str:
    """Render a public-safe card containing metadata rather than source content."""

    return (
        f"# {card.title}\n\n"
        f"- Privacy tier: {card.tier.name}\n"
        f"- Source file: {card.source.name}\n"
        f"- SHA-256: `{card.digest}`\n"
    )
