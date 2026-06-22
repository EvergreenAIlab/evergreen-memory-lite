# Roadmap

The roadmap is intentionally small. Dates and scope may change after public review.

## v0.1.0 — safe local demo foundation

Document the privacy tiers, ship synthetic P0 examples, and demonstrate dry-run-first card generation with local metadata and tests.

## v0.2.0 — shipped: household admin value loop

v0.2.0 shipped the household admin value loop, which turns structured synthetic notes into a readable local brief, action list, timeline, source index, and risk flags while preserving dry-run and no-source-change guarantees.

## v0.3.0 — shipped: local search and source memory

v0.3.0 shipped an inspectable SQLite index, readable memory overview, and source-traceable keyword and metadata filters over synthetic demo data. It remains cloud-free and uses no AI, RAG, embeddings, or vector database.

## v0.4.0 — shipped: document intake and local launcher

v0.4.0 shipped local intake for `.txt`, `.md`, `.docx`, and digital `.pdf` files, plus a static dashboard and simple Windows launcher. It remains local-only and keeps OCR, .doc, and cloud integrations out of scope.

## Later

Consider optional integrations only after privacy boundaries, threat modeling, and maintainer capacity mature. Workflows involving real sensitive data are out of scope for the current release and near-term roadmap.
