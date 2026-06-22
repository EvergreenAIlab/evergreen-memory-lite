from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from evergreen_memory_lite.intake import (
    EXTRACTION_REPORT_NAME,
    EXTRACTED_DIR_NAME,
    SKIPPED_FILES_NAME,
    extract_docx,
    extract_documents,
    extract_pdf,
    render_extraction_report,
    render_skipped_files,
    scan_inbox,
)
from evergreen_memory_lite.search import SEARCH_INDEX_NAME, query_search_index
from evergreen_memory_lite.runner import run


def file_hashes(directory: Path) -> dict[Path, str]:
    return {
        path.relative_to(directory): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in directory.rglob("*")
        if path.is_file()
    }


def write_docx(path: Path, paragraphs: list[str]) -> None:
    body = "".join(f"<w:p><w:r><w:t>{escape(paragraph)}</w:t></w:r></w:p>" for paragraph in paragraphs)
    document_xml = (
        "<?xml version='1.0' encoding='UTF-8' standalone='yes'?>"
        "<w:document xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'>"
        f"<w:body>{body}<w:sectPr/></w:body>"
        "</w:document>"
    )
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("word/document.xml", document_xml)


def write_pdf(path: Path, text: str) -> None:
    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

    writer = PdfWriter()
    page = writer.add_blank_page(width=300, height=200)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    font_ref = writer._add_object(font)
    content = DecodedStreamObject()
    content.set_data(f"BT /F1 18 Tf 24 120 Td ({text}) Tj ET".encode("latin-1"))
    content_ref = writer._add_object(content)
    page[NameObject("/Contents")] = content_ref
    page[NameObject("/Resources")] = DictionaryObject({NameObject("/Font"): DictionaryObject({NameObject("/F1"): font_ref})})
    with path.open("wb") as stream:
        writer.write(stream)


def make_inbox(tmp_path: Path) -> Path:
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    (inbox / "note.txt").write_text("Plain text intake note\n", encoding="utf-8")
    (inbox / "note.md").write_text("# Markdown intake note\n\nExtra context\n", encoding="utf-8")
    write_docx(inbox / "note.docx", ["DOCX intake note", "Second paragraph"])
    write_pdf(inbox / "note.pdf", "PDF intake note")
    (inbox / "legacy.doc").write_text("legacy binary placeholder", encoding="utf-8")
    (inbox / "image.png").write_bytes(b"not an image, just a placeholder")
    (inbox / "empty.txt").write_text("", encoding="utf-8")
    return inbox


def test_scan_inbox_separates_supported_and_skipped_files(tmp_path: Path) -> None:
    inbox = make_inbox(tmp_path)

    supported, skipped = scan_inbox(inbox)

    assert {item.path.suffix for item in supported} == {".txt", ".md", ".docx", ".pdf"}
    assert any(item.path.name == "legacy.doc" for item in skipped)
    assert any(item.path.name == "image.png" for item in skipped)
    assert any(item.path.name == "empty.txt" for item in skipped)
    assert all(item.size_bytes > 0 for item in supported)


def test_docx_and_pdf_extraction(tmp_path: Path) -> None:
    inbox = make_inbox(tmp_path)

    assert "DOCX intake note" in extract_docx(inbox / "note.docx")
    assert "PDF intake note" in extract_pdf(inbox / "note.pdf")


def test_document_intake_dry_run_writes_nothing(tmp_path: Path) -> None:
    inbox = make_inbox(tmp_path)
    before = file_hashes(inbox)
    output = tmp_path / "output" / "latest"

    result = run(inbox, output, document_intake=True, household_admin=True)

    assert result.dry_run is True
    assert not output.exists()
    assert file_hashes(inbox) == before
    assert {path.name for path in result.intake_outputs} == {
        "note.txt.extracted.md",
        "note.md.extracted.md",
        "note.docx.extracted.md",
        "note.pdf.extracted.md",
        EXTRACTION_REPORT_NAME,
        SKIPPED_FILES_NAME,
        "dashboard.html",
    }
    assert any(path.name.endswith(".extracted.md") for path in result.intake_outputs)


def test_document_intake_write_creates_expected_outputs(tmp_path: Path) -> None:
    inbox = make_inbox(tmp_path)
    before = file_hashes(inbox)
    output = tmp_path / "output" / "latest"

    result = run(inbox, output, write=True, document_intake=True, household_admin=True)

    assert result.dry_run is False
    assert (output / "dashboard.html").is_file()
    assert (output / EXTRACTION_REPORT_NAME).is_file()
    assert (output / SKIPPED_FILES_NAME).is_file()
    assert (output / EXTRACTED_DIR_NAME).is_dir()
    assert any(path.name.endswith(".extracted.md") for path in (output / EXTRACTED_DIR_NAME).iterdir())
    assert (output / "memory_index.md").is_file()
    assert (output / "search_index.sqlite").is_file()
    assert (output / "family_brief.md").is_file()
    assert (output / "action_list.md").is_file()
    assert (output / "timeline.md").is_file()
    assert (output / "source_index.md").is_file()
    assert (output / "risk_flags.md").is_file()
    assert file_hashes(inbox) == before

    extraction = (output / EXTRACTION_REPORT_NAME).read_text(encoding="utf-8")
    skipped = (output / SKIPPED_FILES_NAME).read_text(encoding="utf-8")
    assert "Extracted documents" in extraction
    assert "legacy.doc" in skipped


def test_search_finds_text_from_extracted_documents(tmp_path: Path) -> None:
    inbox = make_inbox(tmp_path)
    output = tmp_path / "output" / "latest"

    run(inbox, output, write=True, document_intake=True, household_admin=True)

    results = query_search_index(output / SEARCH_INDEX_NAME, query="PDF intake note", limit=10)
    assert results
    assert any("PDF intake note" in record.text for record in results)
    assert any(record.source_file == "note.pdf" for record in results)


def test_render_helpers_support_empty_lists(tmp_path: Path) -> None:
    inbox = tmp_path / "empty"
    inbox.mkdir()
    report = extract_documents(inbox, tmp_path / "output")
    assert "Extraction Report" in render_extraction_report(report)
    assert "Skipped Files" in render_skipped_files([])
