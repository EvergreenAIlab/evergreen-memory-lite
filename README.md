# Evergreen Memory Lite

[![CI](https://github.com/EvergreenAIlab/evergreen-memory-lite/actions/workflows/ci.yml/badge.svg)](https://github.com/EvergreenAIlab/evergreen-memory-lite/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Evergreen Memory Lite is a small, Windows-first starter kit for exploring privacy-tiered local memory workflows. It is intended for families and small private offices that want an understandable, local-only demonstration before deciding how a real system should be designed.

The project uses only synthetic P0 examples. It has no cloud dependency, does not call an AI service, and never deletes or changes source files.

**Status:** early v0.1.0 release candidate. The project is an educational demo, not a production-ready system for real sensitive data.

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

## Project layout

```text
data/synthetic/                 Synthetic P0 notes
docs/                           Privacy, architecture, and release guidance
src/evergreen_memory_lite/      Local runner and supporting modules
tests/                          Safety and behavior tests
```

Contributions are welcome when they remain small, local-first, and safe for a public repository. Read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting material.
