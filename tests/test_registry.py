import sqlite3
from pathlib import Path

from evergreen_memory_lite.registry import initialize_registry


def test_registry_initializes_in_temporary_directory(tmp_path: Path) -> None:
    registry = tmp_path / "nested" / "registry.sqlite"

    initialize_registry(registry)

    assert registry.is_file()
    with sqlite3.connect(registry) as connection:
        table = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'cards'"
        ).fetchone()
    assert table == ("cards",)
