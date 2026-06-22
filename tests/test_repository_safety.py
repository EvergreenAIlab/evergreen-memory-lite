import re
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


def test_all_public_text_contains_no_private_identifiers_or_secret_values() -> None:
    private_identifiers = [
        "Jason" + " Li",
        "Li" + " Jin",
        "Bing" + " Zhao",
        "Evergreen Invest" + " AS",
        "933" + "962679",
        "Nord" + "net",
        "Bank" + "ID",
        "TO" + "MRA",
        "China" + " Trip",
        "OSE" + " Radar",
        "Quantamental" + " Radar",
    ]
    credential_keys = [
        "api" + r"[_-]?" + "key",
        "to" + "ken",
        "pass" + "word",
        "pass" + "wd",
        "private" + r"[_-]?" + "key",
    ]
    assigned_value = re.compile(
        rf"(?:{'|'.join(credential_keys)})\s*[:=]\s*[\"']?[^\s\"']+",
        re.IGNORECASE,
    )
    token_prefixes = ["s" + "k-", "xox" + "b-"]

    for path in tracked_candidate_files():
        if path.suffix.lower() not in {".md", ".py", ".toml", ".yml", ".yaml", ".txt"}:
            continue
        text = path.read_text(encoding="utf-8")
        assert all(term.casefold() not in text.casefold() for term in private_identifiers), path
        assert assigned_value.search(text) is None, path
        assert all(prefix.casefold() not in text.casefold() for prefix in token_prefixes), path


def test_data_directory_contains_only_synthetic_markdown() -> None:
    data_files = [path for path in (ROOT / "data").rglob("*") if path.is_file()]
    assert data_files
    assert all(path.parent == ROOT / "data" / "synthetic" for path in data_files)
    assert all(path.suffix == ".md" for path in data_files)


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
