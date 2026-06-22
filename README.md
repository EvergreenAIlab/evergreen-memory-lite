# Evergreen Memory Lite

[![CI](https://github.com/EvergreenAIlab/evergreen-memory-lite/actions/workflows/ci.yml/badge.svg)](https://github.com/EvergreenAIlab/evergreen-memory-lite/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Evergreen Memory Lite is a small, Windows-first starter kit for exploring privacy-tiered local memory workflows. It is intended for families and small private offices that want an understandable, local-only demonstration before deciding how a real system should be designed.

The project uses only synthetic P0 examples. It has no cloud dependency, does not call an AI service, and never deletes or changes source files.

**Status:** v0.1.0 initial public release. The project is an educational demo, not a production-ready system for real sensitive data.

## Why Windows-first

Many households and small offices already organize files in Windows folders and use PowerShell. The starter kit therefore uses `pathlib`, UTF-8 text, ordinary folders, and commands that run directly in PowerShell without Docker, Linux, or WSL.

## Privacy tiers

- **P0 — public or synthetic:** safe demo material created for public use.
- **P1 — low-sensitivity operational:** routine information with limited impact if disclosed.
- **P2 — personal, low risk:** personal context that still requires deliberate handling.
- **P3 — sensitive private:** information requiring strict access controls.
- **P4 — highly sensitive:** identity, health, money, or legal information requiring the strongest protections.

See [docs/privacy_model.md](docs/privacy_model.md) for the handling rules. This repository ships P0 synthetic data only.

## Safety model

Dry-run is the default. A scan reports what would be processed but creates no output. Writing cards requires the explicit `--write` flag. The runner never deletes, moves, renames, overwrites, or mutates source files. Existing card files cause the write to stop rather than overwrite data.

This starter kit can scan Markdown notes, read explicit P0–P4 labels, create simple local cards, record local SQLite metadata, and append a local audit event. It cannot determine whether arbitrary content is truly safe, secure a production deployment, anonymize real documents, or replace professional privacy review.

> **Warning:** Never use real sensitive files in demo mode. Copy only deliberately created synthetic P0 examples into the demo folder.

## Quick start in PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m evergreen_memory_lite.runner --input data\synthetic
```

The final command is a dry run. It prints the planned cards without creating files.

To run the synthetic write demonstration explicitly:

```powershell
.\.venv\Scripts\python.exe -m evergreen_memory_lite.runner `
  --input data\synthetic `
  --output output\cards `
  --write
```

Generated cards, the registry, and the audit log stay under the ignored `output\` directory.

## Household admin value loop (v0.2.0)

The household admin workflow turns a few structured synthetic notes into useful local outputs for a family or small office. It creates a brief, action list, timeline, source index, and risk flags alongside the generated cards. UTF-8 note content may be English, Chinese, Norwegian, or mixed-language.

```powershell
.\.venv\Scripts\python.exe -m evergreen_memory_lite.runner `
  --input data\synthetic `
  --output output\household_admin `
  --household-admin `
  --write
```

Open these files after the command finishes:

- `family_brief.md` — what matters, upcoming items, and a risk summary.
- `action_list.md` — tasks, owners, due dates, status, and context.
- `timeline.md` — dated events and related actions.
- `source_index.md` — source-to-output traceability.
- `risk_flags.md` — privacy, missing-field, and safety reminders.

Omit `--write` to preview the plan without creating anything. Metadata keys remain English and the parser extracts only fixed structured headings; it does not translate or understand arbitrary language semantically. The workflow uses no cloud or API, and source files are never changed. Use only deliberately synthetic P0 notes; real sensitive data is not supported. See [docs/household_admin.md](docs/household_admin.md) for the input format and output guide.

## Local search and source memory (v0.3.0)

The household admin command now also creates `memory_index.md`, a readable overview, and `search_index.sqlite`, a local source-traceable index. Search uses simple SQLite substring and metadata filters; there is no LLM, RAG, vector database, embedding, or cloud service.

```powershell
.\.venv\Scripts\python.exe -m evergreen_memory_lite.search `
  --memory output\household_admin `
  --query kvittering

.\.venv\Scripts\python.exe -m evergreen_memory_lite.search `
  --memory output\household_admin `
  --item-type action `
  --date-from 2026-07-01 `
  --date-to 2026-07-31

.\.venv\Scripts\python.exe -m evergreen_memory_lite.search `
  --memory output\household_admin `
  --category 家务整理
```

Results show their source file, generated output, relevant date, and privacy tier. Search preserves English, Chinese, and Norwegian UTF-8 text without translation or fuzzy matching. See [docs/search.md](docs/search.md) for all filters and limitations.

## Project layout

```text
data/synthetic/                 Synthetic P0 notes
docs/                           Privacy, workflow, architecture, and release guidance
src/evergreen_memory_lite/      Local runner and supporting modules
tests/                          Safety and behavior tests
```

Contributions are welcome when they remain small, local-first, and safe for a public repository. Read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting material.
