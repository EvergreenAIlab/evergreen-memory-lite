import hashlib
from pathlib import Path

from evergreen_memory_lite.runner import run
from evergreen_memory_lite.search import SEARCH_INDEX_NAME, main, query_search_index


ROOT = Path(__file__).resolve().parents[1]


def hashes(directory: Path) -> dict[str, str]:
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in directory.glob("*.md")
    }


def generated_memory(tmp_path: Path) -> tuple[Path, dict[str, str]]:
    inbox = ROOT / "data" / "synthetic"
    before = hashes(inbox)
    output = tmp_path / "output" / "household_admin"
    run(inbox, output, write=True, household_admin=True)
    assert hashes(inbox) == before
    return output, before


def test_search_index_contains_all_types_and_traceability(tmp_path: Path) -> None:
    memory, _ = generated_memory(tmp_path)
    results = query_search_index(memory / SEARCH_INDEX_NAME, limit=100)

    assert {record.item_type for record in results} == {"source", "card", "action", "event", "risk"}
    assert all(record.source_file for record in results)
    assert all(record.output_file for record in results)
    assert all(record.privacy_tier == "P0" for record in results)


def test_utf8_substring_search_finds_english_chinese_and_norwegian(tmp_path: Path) -> None:
    memory, _ = generated_memory(tmp_path)
    index = memory / SEARCH_INDEX_NAME

    assert query_search_index(index, query="museum")
    assert query_search_index(index, query="收纳箱")
    assert query_search_index(index, query="kvittering")


def test_metadata_and_date_filters(tmp_path: Path) -> None:
    memory, _ = generated_memory(tmp_path)
    index = memory / SEARCH_INDEX_NAME

    actions = query_search_index(index, item_type="action", limit=100)
    assert actions and all(item.item_type == "action" for item in actions)
    assert query_search_index(index, category="家务整理")
    assert query_search_index(index, owner="Nora Eksempel")
    assert query_search_index(index, status="计划中")
    assert query_search_index(index, privacy_tier="P0")
    july_actions = query_search_index(
        index, item_type="action", date_from="2026-07-01", date_to="2026-07-31", limit=100
    )
    assert july_actions
    assert all("2026-07-01" <= item.due_date <= "2026-07-31" for item in july_actions)


def test_search_cli_prints_source_and_privacy(tmp_path: Path, capsys) -> None:
    memory, _ = generated_memory(tmp_path)

    assert main(["--memory", str(memory), "--query", "kvittering", "--limit", "2"]) == 0

    output = capsys.readouterr().out
    assert "Source:" in output
    assert "Privacy: P0" in output
    assert "kvittering" in output.casefold()
