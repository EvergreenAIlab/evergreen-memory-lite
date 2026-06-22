"""Local SQLite metadata registry."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from .cards import Card


def initialize_registry(path: Path) -> None:
    """Create the registry and its minimal schema if needed."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS cards (
                source_path TEXT PRIMARY KEY,
                card_path TEXT NOT NULL,
                privacy_tier TEXT NOT NULL,
                source_sha256 TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )


def register_card(path: Path, card: Card, created_at: str) -> None:
    """Register newly created card metadata without storing source content."""

    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            INSERT INTO cards (
                source_path, card_path, privacy_tier, source_sha256, created_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (str(card.source), str(card.destination), card.tier.name, card.digest, created_at),
        )
