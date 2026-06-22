"""Local document intake for TXT, Markdown, DOCX, and digital PDFs.

This module stays conservative by design:
- no OCR
- no old .doc parsing
- no source mutation
- no cloud/API
- no AI, RAG, or vector processing
"""

from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree


SUPPORTED_SUFFIXES = frozenset({".txt", ".md", ".docx", ".pdf"})
DEFAULT_MAX_BYTES = 5_000_000
DEFAULT_MAX_PDF_PAGES = 30
EXTRACTION_REPORT_NAME = "extraction_report.md"
SKIPPED_FILES_NAME = "skipped_files.md"
EXTRACTED_DIR_NAME = "extracted"


@dataclass(frozen=True)
class IntakeFile:
    path: Path
    suffix: str
    size_bytes: int


@dataclass(frozen=True)
class ExtractedDocument:
    source: Path
    source_type: str
    title: str
    category: str
    text: str
    extracted_markdown: str
    extracted_path: Path


@dataclass(frozen=True)
class SkippedFile:
    path: Path
    reason: str


@dataclass(frozen=True)
class IntakeReport:
    input_dir: Path
    output_dir: Path
    generated_at: str
    extracted: tuple[ExtractedDocument, ...]
    skipped: tuple[SkippedFile, ...]


def scan_inbox(input_dir: Path, max_bytes: int = DEFAULT_MAX_BYTES) -> tuple[list[IntakeFile], list[SkippedFile]]:
    """Scan the inbox directory and separate supported files from skipped ones."""

    if not input_dir.is_dir():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")

    files: list[IntakeFile] = []
    skipped: list[SkippedFile] = []
    for path in sorted(input_dir.iterdir(), key=lambda item: item.name.casefold()):
        if path.is_dir():
            skipped.append(SkippedFile(path, "Directory input is not supported in v0.4."))
            continue
        if not path.is_file():
            skipped.append(SkippedFile(path, "Not a regular file."))
            continue
        suffix = path.suffix.casefold()
        if suffix not in SUPPORTED_SUFFIXES:
            skipped.append(
                SkippedFile(
                    path,
                    f"Unsupported suffix {path.suffix or '(none)'}; supported: .txt, .md, .docx, .pdf.",
                )
            )
            continue
        size = path.stat().st_size
        if size == 0:
            skipped.append(SkippedFile(path, "Empty file."))
            continue
        if size > max_bytes:
            skipped.append(SkippedFile(path, f"File is larger than {max_bytes} bytes."))
            continue
        files.append(IntakeFile(path=path, suffix=suffix, size_bytes=size))
    return files, skipped


def extract_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def extract_markdown(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def extract_docx(path: Path) -> str:
    """Extract paragraph text from a DOCX using stdlib zip/xml only."""

    try:
        with zipfile.ZipFile(path) as archive:
            xml_bytes = archive.read("word/document.xml")
    except KeyError as exc:
        raise ValueError("DOCX is missing word/document.xml.") from exc
    except zipfile.BadZipFile as exc:
        raise ValueError("Invalid or corrupt DOCX file.") from exc

    try:
        root = ElementTree.fromstring(xml_bytes)
    except ElementTree.ParseError as exc:
        raise ValueError("DOCX document.xml could not be parsed.") from exc

    namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    paragraphs: list[str] = []
    for paragraph in root.iter(f"{namespace}p"):
        chunks: list[str] = []
        for text_node in paragraph.iter(f"{namespace}t"):
            if text_node.text:
                chunks.append(text_node.text)
        line = "".join(chunks).strip()
        if line:
            paragraphs.append(line)

    if not paragraphs:
        raise ValueError("DOCX has no extractable paragraph text.")
    return "\n\n".join(paragraphs)


def extract_pdf(path: Path, max_pages: int = DEFAULT_MAX_PDF_PAGES) -> str:
    """Extract text from a digital PDF. OCR is intentionally not supported."""

    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise ValueError("PDF support requires pypdf.") from exc

    try:
        reader = PdfReader(str(path))
    except Exception as exc:  # pypdf exceptions vary by version
        raise ValueError(f"PDF could not be opened: {exc}") from exc

    if getattr(reader, "is_encrypted", False):
        raise ValueError("Encrypted PDF is not supported in v0.4.")

    pages = list(reader.pages)
    if len(pages) > max_pages:
        raise ValueError(f"PDF has {len(pages)} pages; v0.4 limit is {max_pages} pages.")

    chunks: list[str] = []
    for index, page in enumerate(pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception as exc:
            raise ValueError(f"Could not extract text from PDF page {index}: {exc}") from exc
        text = text.strip()
        if text:
            chunks.append(f"## Page {index}\n\n{text}")

    if not chunks:
        raise ValueError("PDF has no extractable text; OCR is not supported in v0.4.")
    return "\n\n".join(chunks)


def extract_documents(input_dir: Path, output_dir: Path, *, max_bytes: int = DEFAULT_MAX_BYTES, max_pdf_pages: int = DEFAULT_MAX_PDF_PAGES) -> IntakeReport:
    """Extract supported inbox documents without writing anything."""

    input_dir = input_dir.resolve()
    output_dir = output_dir.resolve()
    generated_at = datetime.now(timezone.utc).isoformat()
    intake_files, skipped = scan_inbox(input_dir, max_bytes=max_bytes)
    extracted: list[ExtractedDocument] = []

    for intake_file in intake_files:
        try:
            if intake_file.suffix == ".txt":
                raw_text = extract_txt(intake_file.path)
                source_type = "txt"
            elif intake_file.suffix == ".md":
                raw_text = extract_markdown(intake_file.path)
                source_type = "markdown"
            elif intake_file.suffix == ".docx":
                raw_text = extract_docx(intake_file.path)
                source_type = "docx"
            elif intake_file.suffix == ".pdf":
                raw_text = extract_pdf(intake_file.path, max_pages=max_pdf_pages)
                source_type = "pdf"
            else:  # pragma: no cover - guarded by scan_inbox
                raise ValueError(f"Unsupported suffix {intake_file.suffix}.")
        except (UnicodeDecodeError, OSError, ValueError) as exc:
            skipped.append(SkippedFile(intake_file.path, str(exc)))
            continue

        title = _title_from_text(raw_text) or intake_file.path.stem
        category = _infer_category(intake_file.path.name)
        extracted_path = output_dir / EXTRACTED_DIR_NAME / f"{_safe_stem(intake_file.path.name)}.extracted.md"
        extracted_markdown = render_extracted_markdown(
            source=intake_file.path,
            source_type=source_type,
            title=title,
            category=category,
            extracted_text=raw_text,
            generated_at=generated_at,
        )
        extracted.append(
            ExtractedDocument(
                source=intake_file.path,
                source_type=source_type,
                title=title,
                category=category,
                text=raw_text,
                extracted_markdown=extracted_markdown,
                extracted_path=extracted_path,
            )
        )

    return IntakeReport(
        input_dir=input_dir,
        output_dir=output_dir,
        generated_at=generated_at,
        extracted=tuple(extracted),
        skipped=tuple(skipped),
    )


def render_extracted_markdown(
    *,
    source: Path,
    source_type: str,
    title: str,
    category: str,
    extracted_text: str,
    generated_at: str,
) -> str:
    """Render a conservative Markdown note from extracted content."""

    body = extracted_text.strip() or "_No extractable text._"
    return (
        "---\n"
        "privacy_tier: P1\n"
        "synthetic: false\n"
        f"category: {category}\n"
        f"title: {title}\n"
        "status: needs_review\n"
        "---\n\n"
        f"# {title}\n\n"
        "Document intake note generated locally from an inbox file.\n\n"
        "Risks:\n"
        "- Review this extracted document before treating it as reliable memory.\n"
        "- Real sensitive data is not supported in v0.4.\n\n"
        "## Extraction metadata\n\n"
        f"- source_file: `{source.name}`\n"
        f"- source_type: `{source_type}`\n"
        f"- generated_at: `{generated_at}`\n"
        "- extraction_status: `needs_review`\n"
        "- limitations: no OCR, no semantic understanding, no AI.\n\n"
        "## Extracted text\n\n"
        f"{body}\n"
    )


def render_extraction_report(report: IntakeReport) -> str:
    lines = [
        "# Extraction Report",
        "",
        f"- Input directory: `{report.input_dir}`",
        f"- Output directory: `{report.output_dir}`",
        f"- Generated at: `{report.generated_at}`",
        f"- Extracted documents: **{len(report.extracted)}**",
        f"- Skipped files: **{len(report.skipped)}**",
        "- Source files changed: **0**",
        "",
        "## Extracted documents",
        "",
        "| Source | Type | Extracted preview |",
        "| --- | --- | --- |",
    ]
    if report.extracted:
        for document in report.extracted:
            lines.append(f"| `{document.source.name}` | {document.source_type} | `{document.extracted_path.name}` |")
    else:
        lines.append("| — | — | — |")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- DOCX extraction reads paragraph text only.",
            "- PDF extraction supports digital PDFs with selectable text only.",
            "- OCR and scanned PDFs are not supported in v0.4.",
            "",
        ]
    )
    return "\n".join(lines)


def render_skipped_files(skipped: Iterable[SkippedFile]) -> str:
    skipped_list = list(skipped)
    lines = [
        "# Skipped Files",
        "",
        "| File | Reason |",
        "| --- | --- |",
    ]
    if skipped_list:
        for item in skipped_list:
            lines.append(f"| `{item.path.name}` | {_escape_table(item.reason)} |")
    else:
        lines.append("| — | No skipped files |")
    lines.append("")
    return "\n".join(lines)


def write_intake_outputs(report: IntakeReport) -> tuple[Path, ...]:
    """Write extraction outputs and reports without overwriting existing files."""

    extracted_dir = report.output_dir / EXTRACTED_DIR_NAME
    extracted_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    for document in report.extracted:
        if document.extracted_path.exists():
            raise FileExistsError(f"Refusing to overwrite extracted preview: {document.extracted_path}")
        document.extracted_path.write_text(document.extracted_markdown, encoding="utf-8", newline="\n")
        written.append(document.extracted_path)

    for name, content in (
        (EXTRACTION_REPORT_NAME, render_extraction_report(report)),
        (SKIPPED_FILES_NAME, render_skipped_files(report.skipped)),
    ):
        path = report.output_dir / name
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite intake report: {path}")
        path.write_text(content, encoding="utf-8", newline="\n")
        written.append(path)

    return tuple(written)


def _title_from_text(text: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped.lstrip("#").strip()[:120]
    return None


def _infer_category(name: str) -> str:
    lowered = name.casefold()
    if any(word in lowered for word in ("receipt", "kvittering", "invoice", "faktura", "收据", "发票")):
        return "receipt"
    if any(word in lowered for word in ("travel", "trip", "reise", "旅行", "行程")):
        return "travel"
    if any(word in lowered for word in ("task", "todo", "household", "oppgave", "待办", "家务")):
        return "household"
    return "document"


def _safe_stem(value: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._-")
    return stem or "document"


def _escape_table(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()
