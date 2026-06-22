from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def tracked_candidate_files() -> list[Path]:
    excluded_parts = {".git", ".venv", "__pycache__", ".pytest_cache", "output"}
    return [
        path
        for path in ROOT.rglob("*")
        if path.is_file() and not excluded_parts.intersection(path.relative_to(ROOT).parts)
    ]


def test_synthetic_samples_are_marked_and_contain_no_forbidden_identifiers() -> None:
    samples = sorted((ROOT / "data" / "synthetic").glob("*.md"))
    assert samples
    forbidden = [
        "Jason" + " Li",
        "Li" + " Jin",
        "Bing" + " Zhao",
        "Evergreen Invest" + " AS",
        "Nord" + "net",
        "Bank" + "ID",
    ]
    for sample in samples:
        text = sample.read_text(encoding="utf-8")
        assert "Privacy: P0" in text
        assert "Synthetic: true" in text
        assert all(term.casefold() not in text.casefold() for term in forbidden)


def test_forbidden_private_paths_are_absent() -> None:
    forbidden_paths = [
        "C:" + "\\EvergreenAI",
        "C:" + "\\dev\\evergreen-os",
        "C:" + "\\research",
        "C:" + "\\reaserch",
    ]
    for path in tracked_candidate_files():
        if path.suffix.lower() not in {".md", ".py", ".toml", ".yml", ".yaml", ".txt"}:
            continue
        text = path.read_text(encoding="utf-8")
        assert all(term.casefold() not in text.casefold() for term in forbidden_paths), path
