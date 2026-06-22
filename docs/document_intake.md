# Document Intake

v0.4.0 adds local document intake for ordinary files.

## Supported files

- `.txt`
- `.md`
- `.docx`
- digital `.pdf` files with selectable text

## Unsupported files

- old `.doc`
- scanned PDFs
- images
- OCR
- encrypted PDFs
- email/cloud/bot ingestion

## Workflow

1. Put files in `inbox/`.
2. Run `Run Evergreen Memory Lite.bat`.
3. Click `Run inbox`.
4. Open `output/latest/dashboard.html`.

## Outputs

- `extraction_report.md`
- `skipped_files.md`
- `extracted/*.extracted.md`
- household reports
- `memory_index.md`
- `search_index.sqlite`
- `dashboard.html`

## Boundaries

The system extracts text locally and conservatively. It does not understand arbitrary documents semantically. It does not OCR images or scanned PDFs. It does not use AI, cloud services, RAG, embeddings, or vector databases.

Source files are not deleted, moved, renamed, or modified.

Review extracted text before relying on it.
