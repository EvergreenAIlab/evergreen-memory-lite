"""Simple Windows-first local launcher.

This is a minimal operation panel, not a chat interface.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tkinter as tk
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, simpledialog

from .search import SEARCH_INDEX_NAME, query_search_index


ROOT = Path.cwd()
INBOX = ROOT / "inbox"
OUTPUT = ROOT / "output" / "latest"
SUPPORTED_FILETYPES = [
    ("Supported documents", "*.txt *.md *.docx *.pdf"),
    ("Text", "*.txt"),
    ("Markdown", "*.md"),
    ("Word DOCX", "*.docx"),
    ("Digital PDF", "*.pdf"),
]


def ensure_dirs() -> None:
    INBOX.mkdir(parents=True, exist_ok=True)
    (ROOT / "output").mkdir(parents=True, exist_ok=True)


def collision_safe_destination(path: Path) -> Path:
    destination = INBOX / path.name
    if not destination.exists():
        return destination
    counter = 2
    while True:
        candidate = INBOX / f"{path.stem}_{counter}{path.suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def add_files() -> None:
    ensure_dirs()
    selected = filedialog.askopenfilenames(title="Add files to Evergreen inbox", filetypes=SUPPORTED_FILETYPES)
    if not selected:
        return
    copied = 0
    for filename in selected:
        source = Path(filename)
        destination = collision_safe_destination(source)
        shutil.copy2(source, destination)
        copied += 1
    messagebox.showinfo("Evergreen Memory Lite", f"Copied {copied} file(s) into inbox.")


def paste_quick_note() -> None:
    ensure_dirs()
    note = simpledialog.askstring("Paste quick note", "Paste a quick note:", parent=None)
    if note is None or not note.strip():
        return
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = INBOX / f"quick_note_{timestamp}.txt"
    path.write_text(note.strip() + "\n", encoding="utf-8", newline="\n")
    messagebox.showinfo("Evergreen Memory Lite", f"Saved {path.name} into inbox.")


def _clear_output_dir() -> None:
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)


def run_inbox() -> None:
    ensure_dirs()
    _clear_output_dir()
    command = [
        sys.executable,
        "-m",
        "evergreen_memory_lite.runner",
        "--input",
        str(INBOX),
        "--output",
        str(OUTPUT),
        "--document-intake",
        "--household-admin",
        "--write",
    ]
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if completed.returncode != 0:
        messagebox.showerror("Run failed", completed.stderr or completed.stdout)
        return
    dashboard = OUTPUT / "dashboard.html"
    if dashboard.is_file():
        webbrowser.open(dashboard.resolve().as_uri())
    messagebox.showinfo("Evergreen Memory Lite", completed.stdout or "Run complete.")


def open_dashboard() -> None:
    dashboard = OUTPUT / "dashboard.html"
    if not dashboard.is_file():
        messagebox.showwarning("Evergreen Memory Lite", "No dashboard found. Run inbox first.")
        return
    webbrowser.open(dashboard.resolve().as_uri())


def search_memory() -> None:
    query = simpledialog.askstring("Search memory", "Search for:")
    if query is None or not query.strip():
        return
    index = OUTPUT / SEARCH_INDEX_NAME
    if not index.is_file():
        messagebox.showwarning("Evergreen Memory Lite", "No search index found. Run inbox first.")
        return
    try:
        records = query_search_index(index, query=query.strip(), limit=20)
    except Exception as exc:
        messagebox.showerror("Search failed", str(exc))
        return
    window = tk.Toplevel()
    window.title("Search results")
    text = scrolledtext.ScrolledText(window, width=100, height=28)
    text.pack(fill="both", expand=True)
    text.insert("end", f"{len(records)} result(s)\n\n")
    for index_number, record in enumerate(records, start=1):
        text.insert("end", f"[{index_number}] {record.item_type.upper()} — {record.title}\n")
        text.insert("end", f"  Source: {record.source_file}\n")
        text.insert("end", f"  Output: {record.output_file}\n")
        text.insert("end", f"  Date: {record.due_date or record.date or '—'}\n")
        text.insert("end", f"  Privacy: {record.privacy_tier}\n\n")
    text.configure(state="disabled")


def main() -> int:
    ensure_dirs()
    root = tk.Tk()
    root.title("Evergreen Memory Lite")
    root.geometry("420x300")

    tk.Label(root, text="Evergreen Memory Lite", font=("Segoe UI", 16, "bold")).pack(pady=(20, 10))
    tk.Label(root, text="Local document intake. No AI, no cloud, no OCR.").pack(pady=(0, 15))

    for label, command in [
        ("Add files", add_files),
        ("Paste quick note", paste_quick_note),
        ("Run inbox", run_inbox),
        ("Search memory", search_memory),
        ("Open latest dashboard", open_dashboard),
        ("Exit", root.destroy),
    ]:
        tk.Button(root, text=label, command=command, width=28).pack(pady=4)

    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
