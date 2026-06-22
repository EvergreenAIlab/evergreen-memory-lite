# Household admin value loop

## What problem it solves

Small household and office notes often contain a mix of tasks, dates, context, and reminders. The household admin value loop turns a folder of structured synthetic notes into five readable local Markdown files. A non-technical user can open them directly to see what matters, what to do next, and where each item came from.

The workflow is deliberately rule-based. It uses plain Python, Markdown, and SQLite so its behavior is inspectable. It does not use an LLM, RAG, NLP library, cloud service, or external API because the current goal is a predictable local foundation with a narrow privacy boundary.

Note content may be English, Chinese, Norwegian, or a mixture. UTF-8 text is preserved in the generated files; the workflow does not translate it or attempt to understand arbitrary language semantically.

## Example input

Each note uses a small frontmatter block followed by optional `Actions`, `Events`, and `Risks` lists:

```markdown
---
privacy_tier: P0
synthetic: true
category: household task
title: Prepare fictional guest room checklist
date: 2026-06-22
due_date: 2026-07-03
owner: Alex Example
status: planned
---

Prepare the imaginary Cedar Room for a fictional weekend visitor.

Actions:
- Add two demo towels to the checklist

Events:
- 2026-07-03: Review the fictional guest room checklist

Risks:
- Keep every person and room detail fictional
```

Metadata field names are fixed in English and dates use `YYYY-MM-DD`. This keeps parsing deterministic across languages. Missing optional action fields and malformed event entries are reported gently in `risk_flags.md`. Unknown or duplicate frontmatter fields are rejected so mistakes remain visible.

The parser recognizes only this small set of section aliases:

| Purpose | Accepted headings |
| --- | --- |
| Actions | `Actions`, `Action items`, `Tasks`, `待办`, `行动`, `Oppgaver`, `Gjøremål` |
| Events | `Events`, `Timeline`, `Key dates`, `事件`, `时间线`, `Hendelser`, `Tidslinje` |
| Risks | `Risks`, `Risk flags`, `Warnings`, `风险`, `风险提示`, `Risiko`, `Varsler` |

Latin headings are matched case-insensitively. Chinese headings are matched exactly after trimming whitespace and a final colon. There is no fuzzy matching, language detection, or semantic inference.

## Run it from PowerShell

```powershell
.\.venv\Scripts\python.exe -m evergreen_memory_lite.runner `
  --input data\synthetic `
  --output output\household_admin `
  --household-admin `
  --write
```

Without `--write`, the same command is a dry run and creates no files.

## Useful local outputs

- `family_brief.md` summarizes note count, key context, upcoming items, risks, and the zero source-change guarantee.
- `action_list.md` lists each action with its owner, due date, source, status, and reason.
- `timeline.md` sorts events by date and connects them to related actions.
- `source_index.md` records title, category, privacy tier, generated card path, and referencing outputs for every source.
- `risk_flags.md` highlights non-P0 notes, missing or ambiguous fields, note-provided reminders, and the privacy boundary.

Cards are stored in `output\household_admin\cards`. The local registry and audit event remain under `output\household_admin`. All of `output\` is ignored by Git.

## Privacy boundary

The repository ships synthetic P0 examples only. A non-P0 note is visibly flagged and is not treated as supported safe input. The parser cannot determine whether arbitrary text is genuinely safe, redact real documents, or secure a production workflow.

Never use real sensitive files with this workflow. The runner reads source notes but never deletes, moves, renames, overwrites, or mutates them; every generated report states that source files changed is zero.
