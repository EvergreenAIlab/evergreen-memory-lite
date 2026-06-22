# Architecture

The demo is a single local Python process with no required cloud service.

```text
inbox/ or data/synthetic/
          |
          v
     local runner ---- dry-run plan (default)
          |
          +---- generated Markdown cards
          +---- registry.sqlite metadata
          +---- audit.jsonl event log
```

- **Inbox:** a user-selected directory of Markdown notes. The repository demonstration points to `data/synthetic/`.
- **Local runner:** finds notes, reads explicit privacy labels, and builds a processing plan. It reads source files but never changes them.
- **Generated cards:** short Markdown records written only after `--write` is supplied. Existing cards are never overwritten.
- **Registry:** local SQLite metadata for generated cards. It contains paths, labels, hashes, and timestamps, not source content.
- **Audit log:** append-only JSON Lines events under the selected output area.
- **Synthetic samples:** small P0 fixtures used by documentation and tests.

Core demo operation requires only Python and the standard library. There is no cloud API, Docker service, background process, vector store, or AI model.
