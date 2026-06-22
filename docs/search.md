# Local search and source memory

## What it solves

The household admin workflow creates useful reports, but users also need to retrieve a remembered action, date, category, owner, or source. Local Search & Source Memory makes those generated items searchable without sending data anywhere.

Running the household admin workflow with `--write` adds two files:

- `memory_index.md` is a plain-language overview of notes, actions, events, risks, privacy tiers, and source links.
- `search_index.sqlite` stores source-traceable records for sources, cards, actions, events, and risks.

Both remain under the ignored output directory. Dry-run mode plans them but writes nothing.

## Search commands

```powershell
.\.venv\Scripts\python.exe -m evergreen_memory_lite.search --memory output\household_admin --query receipt
.\.venv\Scripts\python.exe -m evergreen_memory_lite.search --memory output\household_admin --item-type action
.\.venv\Scripts\python.exe -m evergreen_memory_lite.search --memory output\household_admin --owner "Nora Eksempel"
.\.venv\Scripts\python.exe -m evergreen_memory_lite.search --memory output\household_admin --date-from 2026-07-01 --date-to 2026-07-31
```

Supported filters are `--query`, `--item-type`, `--category`, `--owner`, `--status`, `--privacy-tier`, `--date-from`, `--date-to`, and `--limit`. Filters can be combined. Every result shows item type, title, source file, output file, date or due date, and privacy tier.

## Multilingual behavior

Queries use literal UTF-8 substrings. English, Chinese, and Norwegian synthetic content is preserved and searchable. There is no translation, language detection, fuzzy matching, ranking model, or semantic inference.

## Privacy boundary and limitations

This release is for deliberately synthetic P0 data. Non-P0 notes are flagged and are not treated as supported safe input. The index stores parsed synthetic summaries and fields, not a secure copy of arbitrary documents.

Search is intentionally small: standard-library Python and ordinary SQLite filters. It includes no LLM, RAG, embeddings, vector database, cloud API, server, web UI, bot, or background watcher. Source files remain unchanged.
