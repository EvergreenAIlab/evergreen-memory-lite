# Changelog

All notable changes will be documented here.

## Unreleased

- No unreleased changes.

## 0.4.0 - 2026-06-22

- Added document intake for `.txt`, `.md`, `.docx`, and digital `.pdf` files.
- Added local extraction reports and skipped-file reports.
- Added extracted Markdown previews under `output/latest/extracted/`.
- Added a static local `dashboard.html`.
- Added a simple Windows local launcher.
- Added root-level Windows batch entry points.
- Preserved local-only, no-AI, no-cloud, no-source-mutation behavior.

## 0.3.0 - 2026-06-22

- Added Local Search & Source Memory for generated household admin outputs.
- Added `memory_index.md` to summarize searchable local memory.
- Added a local SQLite `search_index.sqlite` under ignored `output/`.
- Added search CLI filters for keyword, item type, category, owner, status, privacy tier, and date range.
- Added simple UTF-8 substring search across English, Chinese, and Norwegian synthetic content.
- Preserved source traceability, dry-run behavior, and no-source-file-change guarantees.

## 0.2.0 - 2026-06-22

- Added the household admin value loop for structured synthetic P0 notes.
- Added local Markdown outputs: family brief, action list, timeline, source index, and risk flags.
- Added English, Chinese, and Norwegian synthetic samples with UTF-8 preservation.
- Added fixed section heading aliases for actions, events, and risks.
- Preserved dry-run-by-default behavior and no-source-file-change guarantees.
- Added tests for household output generation, non-P0 flagging, source immutability, and multilingual content.

## 0.1.0 - 2026-06-22

- Initial Windows-first, synthetic-only project skeleton.
- Repository templates, maintainer guidance, roadmap, and release preparation.
- Dry-run-by-default local runner with explicit card generation.
- P0-P4 privacy model, local SQLite metadata registry, and audit log.
- Synthetic demonstration notes, pytest coverage, and Windows CI.
