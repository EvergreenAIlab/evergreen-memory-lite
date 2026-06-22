"""Static local dashboard generation.

The dashboard is a local HTML file, not a web app.
No JavaScript, no CDN, no server.
"""

from __future__ import annotations

import html
from pathlib import Path


DASHBOARD_NAME = "dashboard.html"


def render_dashboard(output_dir: Path) -> str:
    files = [
        ("Extraction report", "extraction_report.md"),
        ("Skipped files", "skipped_files.md"),
        ("Family brief", "family_brief.md"),
        ("Action list", "action_list.md"),
        ("Timeline", "timeline.md"),
        ("Source index", "source_index.md"),
        ("Risk flags", "risk_flags.md"),
        ("Memory index", "memory_index.md"),
    ]

    links = []
    for label, filename in files:
        path = output_dir / filename
        status = "available" if path.exists() else "missing"
        links.append(f'<li><a href="{html.escape(filename)}">{html.escape(label)}</a> <span>({status})</span></li>')

    extracted_dir = output_dir / "extracted"
    extracted = sorted(extracted_dir.glob("*.extracted.md")) if extracted_dir.is_dir() else []
    extracted_links = [
        f'<li><a href="extracted/{html.escape(path.name)}">{html.escape(path.name)}</a></li>'
        for path in extracted
    ] or ["<li>No extracted previews found.</li>"]

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Evergreen Memory Lite Dashboard</title>
  <style>
    body {{ font-family: system-ui, -apple-system, Segoe UI, sans-serif; max-width: 960px; margin: 2rem auto; padding: 0 1rem; line-height: 1.5; }}
    code {{ background: #f3f3f3; padding: 0.1rem 0.25rem; border-radius: 0.25rem; }}
    .notice {{ border: 1px solid #ddd; padding: 1rem; border-radius: 0.5rem; background: #fafafa; }}
  </style>
</head>
<body>
  <h1>Evergreen Memory Lite Dashboard</h1>
  <div class="notice">
    <strong>Local-only notice:</strong>
    This dashboard is generated on your computer. v0.4 uses no AI, no cloud, no RAG, no vector database, and no OCR.
  </div>

  <h2>Generated outputs</h2>
  <ul>
    {''.join(links)}
  </ul>

  <h2>Extracted document previews</h2>
  <ul>
    {''.join(extracted_links)}
  </ul>

  <h2>Search examples</h2>
  <pre><code>python -m evergreen_memory_lite.search --memory output\\latest --query receipt
python -m evergreen_memory_lite.search --memory output\\latest --item-type action
python -m evergreen_memory_lite.search --memory output\\latest --privacy-tier P1</code></pre>

  <h2>Boundaries</h2>
  <ul>
    <li>Supported: .txt, .md, .docx, digital .pdf with selectable text.</li>
    <li>Unsupported: .doc, scanned PDF, image OCR, encrypted PDF.</li>
    <li>Source files are not deleted, moved, renamed, or modified.</li>
    <li>Review extracted text before relying on it.</li>
  </ul>
</body>
</html>
"""


def write_dashboard(output_dir: Path) -> Path:
    path = output_dir / DASHBOARD_NAME
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite dashboard: {path}")
    path.write_text(render_dashboard(output_dir), encoding="utf-8", newline="\n")
    return path
