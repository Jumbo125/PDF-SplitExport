"""
PDF-SplitExport UI
Author: Andreas Rottmann
Version: 1.0.0
License: AGPL-3.0-or-later

Funktionen:
- PDF splitten ohne OCR/Bildumwandlung: Text bleibt markierbar, wenn die Quelle echten Text enthält.
- PDF-Seiten als Bilder exportieren: PNG, JPG, TIFF, GIF, WEBP mit DPI und formatabhängigen Optionen.
- Passwortgeschützte PDFs: Passwort-Eingabe plus optionaler Versuch mit leerem Passwort/ohne User-Passwort.

Hinweis zum Schutzmodus:
Dieses Programm knackt keine Passwörter und umgeht keine echte Verschlüsselung.
Der optionale Modus "ohne Passwort versuchen" hilft nur bei PDFs, die zwar Berechtigungs-/Owner-Flags
oder ein leeres User-Passwort haben, technisch aber ohne Passwort geöffnet werden können.
"""

from __future__ import annotations

import os
import re
import sys
import threading
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox
from tkinter import ttk
from typing import Callable, Iterable

from pypdf import PdfReader, PdfWriter

import fitz  # PyMuPDF
from PIL import Image, ImageTk

APP_NAME = "PDF-SplitExport"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Andreas Rottmann"
APP_LICENSE = "AGPL-3.0-or-later"

SUPPORTED_IMAGE_FORMATS = ["PNG", "JPG", "TIFF", "GIF", "WEBP"]


class AutoHideScrollbar(ttk.Scrollbar):
    """
    Blendet die Scrollbar aus, wenn der gesamte Inhalt sichtbar ist.
    """

    def set(self, first, last):
        first_float = float(first)
        last_float = float(last)
        if first_float <= 0.0 and last_float >= 1.0:
            self.grid_remove()
        else:
            self.grid()
        super().set(first, last)


# ============================================================
# Ressourcen / Pfade
# ============================================================


def resource_path(relative_path: str) -> str:
    """
    Findet Ressourcen sowohl im normalen Python-Lauf als auch in PyInstaller-Onefile.
    """
    try:
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)


# ============================================================
# Allgemeine Hilfsfunktionen
# ============================================================


def sanitize_filename_part(text: str) -> str:
    """
    Entfernt Windows-ungültige Zeichen aus Dateinamen.
    """
    text = text.strip()
    text = re.sub(r'[<>:"/\\|?*]', "_", text)
    text = re.sub(r"\s+", " ", text)
    return text or "output"


def make_numbered_pdf_path(base_path: str, number: int) -> str:
    """
    Aus C:/Ordner/ausgabe.pdf wird C:/Ordner/ausgabe_1.pdf usw.
    """
    folder = os.path.dirname(base_path)
    filename = os.path.basename(base_path)
    name, ext = os.path.splitext(filename)
    if not ext:
        ext = ".pdf"
    name = sanitize_filename_part(name)
    return os.path.join(folder, f"{name}_{number}{ext}")


def make_image_output_path(folder: str, prefix: str, page_number: int, seq_number: int, ext: str) -> str:
    """
    Dynamischer Prefix.

    Ohne Platzhalter:
        prefix = scan
        scan_001_seite_001.png

    Mit Platzhaltern:
        {page}  = echte PDF-Seite, z. B. 7
        {page0} = echte PDF-Seite dreistellig, z. B. 007
        {n}     = laufende Nummer, z. B. 1
        {n0}    = laufende Nummer dreistellig, z. B. 001
    """
    prefix = prefix.strip() or "seite"
    ext = ext.lower().replace(".", "")

    context = {
        "page": page_number,
        "page0": f"{page_number:03d}",
        "n": seq_number,
        "n0": f"{seq_number:03d}",
    }

    if "{" in prefix and "}" in prefix:
        try:
            stem = prefix.format(**context)
        except Exception:
            stem = f"{prefix}_{seq_number:03d}_seite_{page_number:03d}"
    else:
        stem = f"{prefix}_{seq_number:03d}_seite_{page_number:03d}"

    stem = sanitize_filename_part(stem)
    return os.path.join(folder, f"{stem}.{ext}")


def parse_positive_int(value: str, name: str) -> int:
    value = value.strip()
    if not value.isdigit():
        raise ValueError(f"{name} muss eine ganze Zahl sein.")
    number = int(value)
    if number < 1:
        raise ValueError(f"{name} muss mindestens 1 sein.")
    return number


def parse_int_in_range(value: str, name: str, minimum: int, maximum: int) -> int:
    number = parse_positive_int(value, name)
    if number < minimum or number > maximum:
        raise ValueError(f"{name} muss zwischen {minimum} und {maximum} liegen.")
    return number


# ============================================================
# Passwort-/Schutz-Hilfen
# ============================================================


@dataclass
class PdfAccessOptions:
    password: str = ""
    try_without_password: bool = True


def try_decrypt_pypdf(reader: PdfReader, options: PdfAccessOptions) -> bool:
    """
    Entsperrt pypdf, wenn möglich.

    Wichtig:
    - Knackt keine Passwörter.
    - Versucht Passwort aus Eingabefeld.
    - Optional versucht leeres Passwort, falls PDF nur Owner-/Permission-Schutz oder leeres User-Passwort hat.
    """
    if not reader.is_encrypted:
        return True

    candidates: list[str] = []
    if options.password:
        candidates.append(options.password)
    if options.try_without_password and "" not in candidates:
        candidates.append("")

    for candidate in candidates:
        try:
            result = reader.decrypt(candidate)
            if result:
                return True
        except Exception:
            continue

    return False


def open_fitz_document(path: str, options: PdfAccessOptions) -> fitz.Document:
    """
    Öffnet eine PDF mit PyMuPDF.

    Der leere-Passwort-Versuch hilft nur bei Dokumenten, die ohne echtes User-Passwort zugänglich sind.
    """
    doc = fitz.open(path)

    if doc.needs_pass:
        candidates: list[str] = []
        if options.password:
            candidates.append(options.password)
        if options.try_without_password and "" not in candidates:
            candidates.append("")

        authenticated = False
        for candidate in candidates:
            try:
                if doc.authenticate(candidate):
                    authenticated = True
                    break
            except Exception:
                continue

        if not authenticated:
            doc.close()
            raise ValueError(
                "Die PDF ist passwortgeschützt. Bitte Passwort eingeben. "
                "Ohne Passwort kann nur gearbeitet werden, wenn die Datei technisch ohne User-Passwort geöffnet werden darf."
            )

    return doc


# ============================================================
# PDF-Split-Funktionen
# ============================================================


def parse_split_pages(text: str, total_pages: int) -> list[int]:
    """
    Eingabe 10,25 bedeutet:
    Teil 1: Seite 1 bis 10
    Teil 2: Seite 11 bis 25
    Teil 3: Seite 26 bis Ende
    """
    pages: list[int] = []
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        if not part.isdigit():
            raise ValueError(f"Ungültige Seitenzahl: {part}")
        page = int(part)
        if page < 1:
            raise ValueError(f"Seite {page} ist ungültig.")
        if page >= total_pages:
            raise ValueError(
                f"Seite {page} ist ungültig. Die PDF hat {total_pages} Seiten. "
                f"Die letzte erlaubte Split-Seite ist {total_pages - 1}."
            )
        pages.append(page)

    if not pages:
        raise ValueError("Bitte mindestens eine Split-Seite eingeben, z. B. 10 oder 10,25.")

    return sorted(set(pages))


def build_ranges(split_pages: list[int], total_pages: int) -> list[tuple[int, int, str]]:
    """
    Baut fortlaufende Seitenbereiche mit 0-basierten Indizes.
    """
    ranges: list[tuple[int, int, str]] = []
    start_index = 0

    for split_page in split_pages:
        end_index = split_page
        label = f"Seite {start_index + 1} bis {end_index}"
        ranges.append((start_index, end_index, label))
        start_index = end_index

    if start_index < total_pages:
        label = f"Seite {start_index + 1} bis Ende"
        ranges.append((start_index, total_pages, label))

    return ranges


def write_pdf_range_pypdf(
    reader: PdfReader,
    start_index: int,
    end_index: int,
    output_path: str,
    progress_callback: Callable[[], None] | None = None,
):
    """
    Schreibt echten PDF-Seitenbereich. Kein Rendern, kein OCR.
    """
    writer = PdfWriter()
    for i in range(start_index, end_index):
        writer.add_page(reader.pages[i])
        if progress_callback:
            progress_callback()
    with open(output_path, "wb") as f:
        writer.write(f)


def write_pdf_range_fitz(
    source_path: str,
    options: PdfAccessOptions,
    start_index: int,
    end_index: int,
    output_path: str,
    progress_callback: Callable[[], None] | None = None,
):
    """
    Fallback mit PyMuPDF: bleibt PDF/Vektor/Text, rendert also NICHT zu Bild.
    Nützlich bei manchen permission-protected PDFs, die pypdf nicht sauber kopiert.
    """
    src = open_fitz_document(source_path, options)
    out = fitz.open()
    try:
        for i in range(start_index, end_index):
            out.insert_pdf(src, from_page=i, to_page=i)
            if progress_callback:
                progress_callback()
        out.save(output_path, garbage=4, deflate=True)
    finally:
        out.close()
        src.close()


# ============================================================
# Bild-Export-Funktionen
# ============================================================


def parse_export_pages(total_pages: int, mode: str, current_page_text: str, range_start_text: str, range_end_text: str) -> list[int]:
    """
    Gibt echte PDF-Seitennummern zurück. Seite 1 = 1.
    """
    if mode == "current":
        page = parse_positive_int(current_page_text, "Aktuelle Seite")
        if page > total_pages:
            raise ValueError(f"Die PDF hat nur {total_pages} Seiten.")
        return [page]

    if mode == "range":
        start_page = parse_positive_int(range_start_text, "Von-Seite")
        end_page = parse_positive_int(range_end_text, "Bis-Seite")
        if start_page > end_page:
            raise ValueError("Von-Seite darf nicht größer als Bis-Seite sein.")
        if end_page > total_pages:
            raise ValueError(f"Die PDF hat nur {total_pages} Seiten.")
        return list(range(start_page, end_page + 1))

    if mode == "all":
        return list(range(1, total_pages + 1))

    raise ValueError("Bitte einen Exportmodus auswählen.")


def render_pdf_page_to_image(doc: fitz.Document, page_number: int, dpi: int) -> Image.Image:
    page = doc.load_page(page_number - 1)
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=matrix, alpha=False)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def save_image(
    image: Image.Image,
    output_path: str,
    file_type: str,
    quality_value: int,
    tiff_compression: str,
):
    """
    Speichert Bild mit formatabhängiger Quality/Compression.

    PNG:  quality_value = compress_level 0-9, 0 größer/schneller, 9 kleiner/langsamer
    JPG:  quality_value = 1-100
    WEBP: quality_value = 0-100
    GIF:  quality_value = Farben 2-256
    TIFF: compression = none, tiff_deflate, lzw, jpeg
    """
    file_type = file_type.upper()

    if file_type == "PNG":
        compression = max(0, min(9, int(quality_value)))
        image.save(output_path, format="PNG", optimize=True, compress_level=compression)
        return

    if file_type == "JPG":
        q = max(1, min(100, int(quality_value)))
        image = image.convert("RGB")
        image.save(output_path, format="JPEG", quality=q, optimize=True, progressive=True)
        return

    if file_type == "WEBP":
        q = max(0, min(100, int(quality_value)))
        image = image.convert("RGB")
        image.save(output_path, format="WEBP", quality=q, method=6)
        return

    if file_type == "GIF":
        colors = max(2, min(256, int(quality_value)))
        gif_image = image.convert("P", palette=Image.ADAPTIVE, colors=colors)
        gif_image.save(output_path, format="GIF")
        return

    if file_type == "TIFF":
        compression = tiff_compression.strip().lower() or "tiff_deflate"
        allowed = {"none", "tiff_deflate", "lzw", "jpeg"}
        if compression not in allowed:
            raise ValueError("TIFF-Kompression muss none, tiff_deflate, lzw oder jpeg sein.")
        if compression == "none":
            image.save(output_path, format="TIFF")
        elif compression == "jpeg":
            q = max(1, min(100, int(quality_value)))
            image = image.convert("RGB")
            image.save(output_path, format="TIFF", compression="jpeg", quality=q)
        else:
            image.save(output_path, format="TIFF", compression=compression)
        return

    raise ValueError(f"Nicht unterstütztes Format: {file_type}")


# ============================================================
# Tkinter App
# ============================================================


class PdfToolApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(f"{APP_NAME} {APP_VERSION}")
        self.root.geometry("920x740")
        self.root.minsize(820, 640)

        self.input_pdf_var = tk.StringVar()
        self.pdf_password_var = tk.StringVar()
        self.try_without_password_var = tk.BooleanVar(value=True)
        self.use_fitz_split_fallback_var = tk.BooleanVar(value=True)

        # Split-Tab
        self.output_base_var = tk.StringVar()
        self.split_pages_var = tk.StringVar()

        # Bild-Export-Tab
        self.image_output_folder_var = tk.StringVar()
        self.image_prefix_var = tk.StringVar()
        self.image_dpi_var = tk.StringVar(value="300")
        self.image_format_var = tk.StringVar(value="PNG")
        self.quality_var = tk.StringVar(value="6")
        self.tiff_compression_var = tk.StringVar(value="tiff_deflate")

        self.export_current_var = tk.BooleanVar(value=True)
        self.export_range_var = tk.BooleanVar(value=False)
        self.export_all_var = tk.BooleanVar(value=False)
        self.current_page_var = tk.StringVar(value="1")
        self.range_start_var = tk.StringVar(value="1")
        self.range_end_var = tk.StringVar(value="1")

        self.split_total_steps = 0
        self.split_current_steps = 0
        self.image_total_steps = 0
        self.image_current_steps = 0

        self._app_icon_photo: ImageTk.PhotoImage | None = None

        self.set_window_icon()
        self.build_ui()

    # ------------------------------------------------------------
    # UI Aufbau
    # ------------------------------------------------------------

    def set_window_icon(self):
        ico_path = resource_path("assets/app.ico")
        png_path = resource_path("assets/app.png")

        if os.path.exists(ico_path):
            try:
                self.root.iconbitmap(ico_path)
                return
            except Exception:
                pass

        if os.path.exists(png_path):
            try:
                img = Image.open(png_path)
                self._app_icon_photo = ImageTk.PhotoImage(img)
                self.root.iconphoto(True, self._app_icon_photo)
            except Exception:
                pass

    def build_ui(self):
        header = ttk.Frame(self.root, padding=(12, 10, 12, 0))
        header.pack(fill="x")

        ttk.Label(
            header,
            text=f"{APP_NAME} {APP_VERSION}",
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w")

        ttk.Label(
            header,
            text=f"Author: {APP_AUTHOR} | License: {APP_LICENSE}",
            foreground="#555555",
        ).pack(anchor="w", pady=(2, 8))

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=12, pady=12)

        self.split_tab = ttk.Frame(notebook)
        self.image_tab = ttk.Frame(notebook)

        notebook.add(self.split_tab, text="PDF splitten")
        notebook.add(self.image_tab, text="Seite als Bild exportieren")

        self.split_tab_content = self.create_scrollable_tab_content(self.split_tab)
        self.image_tab_content = self.create_scrollable_tab_content(self.image_tab)

        self.build_split_tab()
        self.build_image_tab()

    def create_scrollable_tab_content(self, parent: ttk.Frame) -> ttk.Frame:
        container = ttk.Frame(parent)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        canvas = tk.Canvas(container, highlightthickness=0)
        canvas.grid(row=0, column=0, sticky="nsew")

        scrollbar = AutoHideScrollbar(container, orient="vertical", command=canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        canvas.configure(yscrollcommand=scrollbar.set)

        content = ttk.Frame(canvas, padding=12)
        content_window = canvas.create_window((0, 0), window=content, anchor="nw")

        def sync_scrollregion(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def sync_content_width(event):
            canvas.itemconfigure(content_window, width=event.width)

        content.bind("<Configure>", sync_scrollregion)
        canvas.bind("<Configure>", sync_content_width)

        def on_mousewheel(event):
            delta = 0
            if event.delta:
                delta = int(-event.delta / 120)
            elif getattr(event, "num", None) == 4:
                delta = -1
            elif getattr(event, "num", None) == 5:
                delta = 1
            if delta:
                canvas.yview_scroll(delta, "units")

        def bind_mousewheel(_event):
            canvas.bind_all("<MouseWheel>", on_mousewheel)
            canvas.bind_all("<Button-4>", on_mousewheel)
            canvas.bind_all("<Button-5>", on_mousewheel)

        def unbind_mousewheel(_event):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        for widget in (canvas, content):
            widget.bind("<Enter>", bind_mousewheel)
            widget.bind("<Leave>", unbind_mousewheel)

        return content

    def build_shared_pdf_selector(self, parent: ttk.Frame, log_func: Callable[[str], None]):
        frame = ttk.LabelFrame(parent, text="PDF und Schutz")
        frame.pack(fill="x", pady=(0, 12))

        inner = ttk.Frame(frame, padding=8)
        inner.pack(fill="x")

        ttk.Label(inner, text="PDF-Datei:").pack(anchor="w")
        row = ttk.Frame(inner)
        row.pack(fill="x", pady=(2, 8))

        ttk.Entry(row, textvariable=self.input_pdf_var).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Button(row, text="PDF laden", command=lambda: self.select_pdf(log_func)).pack(side="right")

        pw_row = ttk.Frame(inner)
        pw_row.pack(fill="x", pady=(2, 4))
        ttk.Label(pw_row, text="PDF-Passwort, falls vorhanden:").pack(side="left")
        ttk.Entry(pw_row, textvariable=self.pdf_password_var, show="*", width=28).pack(side="left", padx=(8, 0))

        ttk.Checkbutton(
            inner,
            text="Geschützte PDF ohne Passwort versuchen, wenn technisch möglich / leeres User-Passwort",
            variable=self.try_without_password_var,
        ).pack(anchor="w", pady=(3, 0))

        ttk.Checkbutton(
            inner,
            text="Split-Fallback mit PyMuPDF versuchen, falls pypdf bei geschützten PDFs scheitert",
            variable=self.use_fitz_split_fallback_var,
        ).pack(anchor="w", pady=(3, 0))

        ttk.Label(
            inner,
            text="Hinweis: Das knackt keine Passwörter. Es hilft nur bei PDFs, die ohne echtes User-Passwort geöffnet werden können.",
            foreground="#666666",
        ).pack(anchor="w", pady=(4, 0))

    def build_split_tab(self):
        ttk.Label(
            self.split_tab_content,
            text="PDF splitten ohne Bildumwandlung / ohne OCR",
            font=("Segoe UI", 14, "bold"),
        ).pack(anchor="w", pady=(0, 10))

        ttk.Label(
            self.split_tab_content,
            text="Beispiel: 10,25 erzeugt: _1 = Seite 1-10, _2 = Seite 11-25, _3 = Seite 26-Ende.",
        ).pack(anchor="w", pady=(0, 12))

        self.build_shared_pdf_selector(self.split_tab_content, self.log_split)

        output_frame = ttk.Frame(self.split_tab_content)
        output_frame.pack(fill="x", pady=6)
        ttk.Label(output_frame, text="Speicher-Basisdatei:").pack(anchor="w")
        output_row = ttk.Frame(output_frame)
        output_row.pack(fill="x")
        ttk.Entry(output_row, textvariable=self.output_base_var).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Button(output_row, text="Speicherpfad wählen", command=self.select_output_base).pack(side="right")

        split_frame = ttk.Frame(self.split_tab_content)
        split_frame.pack(fill="x", pady=6)
        ttk.Label(split_frame, text="Split nach Seite X, mehrere mit Komma trennen:").pack(anchor="w")
        ttk.Entry(split_frame, textvariable=self.split_pages_var).pack(fill="x")
        ttk.Label(
            split_frame,
            text="Beispiel: 10,25  ->  Seite 1-10 / Seite 11-25 / Seite 26-Ende",
            foreground="#555555",
        ).pack(anchor="w", pady=(3, 0))

        button_frame = ttk.Frame(self.split_tab_content)
        button_frame.pack(fill="x", pady=(16, 8))
        self.split_start_button = ttk.Button(button_frame, text="Splitten starten", command=self.start_split_thread)
        self.split_start_button.pack(side="left")

        progress_frame = ttk.Frame(self.split_tab_content)
        progress_frame.pack(fill="x", pady=(8, 4))
        ttk.Label(progress_frame, text="Fortschritt:").pack(anchor="w")
        self.split_progress = ttk.Progressbar(progress_frame, orient="horizontal", mode="determinate")
        self.split_progress.pack(fill="x", pady=(4, 0))

        self.split_status_var = tk.StringVar(value="Bereit.")
        ttk.Label(self.split_tab_content, textvariable=self.split_status_var).pack(anchor="w", pady=(8, 4))

        self.split_log_text = tk.Text(self.split_tab_content, height=10, wrap="word")
        self.split_log_text.pack(fill="x", pady=(6, 0))
        self.log_split("Bereit. PDF auswählen, Speicher-Basisdatei wählen und Split-Seiten eingeben.")

    def build_image_tab(self):
        ttk.Label(
            self.image_tab_content,
            text="PDF-Seiten als Bild exportieren",
            font=("Segoe UI", 14, "bold"),
        ).pack(anchor="w", pady=(0, 10))

        ttk.Label(
            self.image_tab_content,
            text="Dieser Reiter rendert Seiten als Bild. Text ist danach im Bild nicht mehr markierbar.",
        ).pack(anchor="w", pady=(0, 12))

        self.build_shared_pdf_selector(self.image_tab_content, self.log_image)

        settings_frame = ttk.LabelFrame(self.image_tab_content, text="Bild-Einstellungen")
        settings_frame.pack(fill="x", pady=6)
        settings_inner = ttk.Frame(settings_frame, padding=8)
        settings_inner.pack(fill="x")

        dpi_row = ttk.Frame(settings_inner)
        dpi_row.pack(fill="x", pady=4)
        ttk.Label(dpi_row, text="DPI:", width=24).pack(side="left")
        ttk.Entry(dpi_row, textvariable=self.image_dpi_var, width=12).pack(side="left")

        format_row = ttk.Frame(settings_inner)
        format_row.pack(fill="x", pady=4)
        ttk.Label(format_row, text="Speicherformat:", width=24).pack(side="left")
        self.format_combo = ttk.Combobox(
            format_row,
            textvariable=self.image_format_var,
            values=SUPPORTED_IMAGE_FORMATS,
            state="readonly",
            width=12,
        )
        self.format_combo.pack(side="left")
        self.format_combo.bind("<<ComboboxSelected>>", lambda _event: self.update_quality_ui())

        quality_row = ttk.Frame(settings_inner)
        quality_row.pack(fill="x", pady=4)
        self.quality_label_var = tk.StringVar()
        ttk.Label(quality_row, textvariable=self.quality_label_var, width=24).pack(side="left")
        ttk.Entry(quality_row, textvariable=self.quality_var, width=12).pack(side="left")
        self.quality_hint_var = tk.StringVar()
        ttk.Label(quality_row, textvariable=self.quality_hint_var, foreground="#555555").pack(side="left", padx=(8, 0))

        tiff_row = ttk.Frame(settings_inner)
        tiff_row.pack(fill="x", pady=4)
        ttk.Label(tiff_row, text="TIFF-Kompression:", width=24).pack(side="left")
        self.tiff_combo = ttk.Combobox(
            tiff_row,
            textvariable=self.tiff_compression_var,
            values=["tiff_deflate", "lzw", "jpeg", "none"],
            state="readonly",
            width=16,
        )
        self.tiff_combo.pack(side="left")

        self.update_quality_ui()

        page_frame = ttk.LabelFrame(self.image_tab_content, text="Seiten auswählen")
        page_frame.pack(fill="x", pady=(12, 8))

        current_row = ttk.Frame(page_frame, padding=6)
        current_row.pack(fill="x")
        ttk.Checkbutton(current_row, text="Aktuelle Seite:", variable=self.export_current_var, command=lambda: self.select_export_mode("current")).pack(side="left")
        ttk.Entry(current_row, textvariable=self.current_page_var, width=10).pack(side="left", padx=(8, 0))

        range_row = ttk.Frame(page_frame, padding=6)
        range_row.pack(fill="x")
        ttk.Checkbutton(range_row, text="Seite X bis X:", variable=self.export_range_var, command=lambda: self.select_export_mode("range")).pack(side="left")
        ttk.Label(range_row, text="von").pack(side="left", padx=(8, 4))
        ttk.Entry(range_row, textvariable=self.range_start_var, width=10).pack(side="left")
        ttk.Label(range_row, text="bis").pack(side="left", padx=(8, 4))
        ttk.Entry(range_row, textvariable=self.range_end_var, width=10).pack(side="left")

        all_row = ttk.Frame(page_frame, padding=6)
        all_row.pack(fill="x")
        ttk.Checkbutton(all_row, text="Alles exportieren", variable=self.export_all_var, command=lambda: self.select_export_mode("all")).pack(side="left")

        output_frame = ttk.Frame(self.image_tab_content)
        output_frame.pack(fill="x", pady=6)
        ttk.Label(output_frame, text="Speicherordner:").pack(anchor="w")
        folder_row = ttk.Frame(output_frame)
        folder_row.pack(fill="x")
        ttk.Entry(folder_row, textvariable=self.image_output_folder_var).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Button(folder_row, text="Ordner wählen", command=self.select_image_output_folder).pack(side="right")

        prefix_frame = ttk.Frame(self.image_tab_content)
        prefix_frame.pack(fill="x", pady=6)
        ttk.Label(prefix_frame, text="Dynamischer Prefix:").pack(anchor="w")
        ttk.Entry(prefix_frame, textvariable=self.image_prefix_var).pack(fill="x")
        ttk.Label(
            prefix_frame,
            text="Beispiele: scan -> scan_001_seite_001.png | scan_{page0} -> scan_001.png | export_{n0}_p{page0}",
            foreground="#555555",
        ).pack(anchor="w", pady=(3, 0))

        button_frame = ttk.Frame(self.image_tab_content)
        button_frame.pack(fill="x", pady=(16, 8))
        self.image_start_button = ttk.Button(button_frame, text="Bildexport starten", command=self.start_image_export_thread)
        self.image_start_button.pack(side="left")

        progress_frame = ttk.Frame(self.image_tab_content)
        progress_frame.pack(fill="x", pady=(8, 4))
        ttk.Label(progress_frame, text="Fortschritt:").pack(anchor="w")
        self.image_progress = ttk.Progressbar(progress_frame, orient="horizontal", mode="determinate")
        self.image_progress.pack(fill="x", pady=(4, 0))

        self.image_status_var = tk.StringVar(value="Bereit.")
        ttk.Label(self.image_tab_content, textvariable=self.image_status_var).pack(anchor="w", pady=(8, 4))

        self.image_log_text = tk.Text(self.image_tab_content, height=8, wrap="word")
        self.image_log_text.pack(fill="x", pady=(6, 0))
        self.log_image("Bereit. PDF auswählen, DPI/Format/Seiten wählen und Speicherordner angeben.")

    def update_quality_ui(self):
        fmt = self.image_format_var.get().upper()

        if fmt == "PNG":
            self.quality_label_var.set("PNG-Kompression:")
            self.quality_hint_var.set("0-9, 0 größer/schneller, 9 kleiner/langsamer")
            if not self.quality_var.get().isdigit() or int(self.quality_var.get() or 0) > 9:
                self.quality_var.set("6")
            self.tiff_combo.configure(state="disabled")
        elif fmt == "JPG":
            self.quality_label_var.set("JPG-Qualität:")
            self.quality_hint_var.set("1-100, empfohlen 85-95")
            self.quality_var.set("95")
            self.tiff_combo.configure(state="disabled")
        elif fmt == "WEBP":
            self.quality_label_var.set("WEBP-Qualität:")
            self.quality_hint_var.set("0-100, empfohlen 80-95")
            self.quality_var.set("90")
            self.tiff_combo.configure(state="disabled")
        elif fmt == "GIF":
            self.quality_label_var.set("GIF-Farben:")
            self.quality_hint_var.set("2-256 Farben")
            self.quality_var.set("256")
            self.tiff_combo.configure(state="disabled")
        elif fmt == "TIFF":
            self.quality_label_var.set("TIFF-JPEG-Qualität:")
            self.quality_hint_var.set("nur bei Kompression=jpeg relevant, sonst egal")
            self.quality_var.set("95")
            self.tiff_combo.configure(state="readonly")

    # ------------------------------------------------------------
    # Gemeinsame Aktionen
    # ------------------------------------------------------------

    def access_options(self) -> PdfAccessOptions:
        return PdfAccessOptions(
            password=self.pdf_password_var.get(),
            try_without_password=self.try_without_password_var.get(),
        )

    def select_pdf(self, log_func: Callable[[str], None]):
        path = filedialog.askopenfilename(title="PDF auswählen", filetypes=[("PDF-Dateien", "*.pdf"), ("Alle Dateien", "*.*")])
        if not path:
            return

        self.input_pdf_var.set(path)
        folder = os.path.dirname(path)
        filename = os.path.basename(path)
        name, _ = os.path.splitext(filename)

        self.output_base_var.set(os.path.join(folder, f"{name}_split.pdf"))
        self.image_output_folder_var.set(folder)
        self.image_prefix_var.set(name)

        log_func(f"PDF geladen: {path}")
        self.read_page_count_to_ui(log_func)

    def read_page_count_to_ui(self, log_func: Callable[[str], None]):
        path = self.input_pdf_var.get().strip()
        if not path or not os.path.isfile(path):
            return
        try:
            reader = PdfReader(path)
            if not try_decrypt_pypdf(reader, self.access_options()):
                log_func("PDF ist verschlüsselt. Seitenanzahl eventuell erst nach Passwort-Eingabe verfügbar.")
                return
            total_pages = len(reader.pages)
            log_func(f"Seitenanzahl: {total_pages}")
            self.range_end_var.set(str(total_pages))
        except Exception as e:
            try:
                doc = open_fitz_document(path, self.access_options())
                total_pages = doc.page_count
                doc.close()
                log_func(f"Seitenanzahl: {total_pages}")
                self.range_end_var.set(str(total_pages))
            except Exception:
                log_func(f"PDF konnte noch nicht gelesen werden: {e}")

    def log_split(self, text: str):
        self.split_log_text.insert("end", text + "\n")
        self.split_log_text.see("end")

    def log_image(self, text: str):
        self.image_log_text.insert("end", text + "\n")
        self.image_log_text.see("end")

    # ------------------------------------------------------------
    # Split Tab Aktionen
    # ------------------------------------------------------------

    def select_output_base(self):
        path = filedialog.asksaveasfilename(title="Speicher-Basisdatei wählen", defaultextension=".pdf", filetypes=[("PDF-Dateien", "*.pdf")])
        if path:
            self.output_base_var.set(path)
            self.log_split(f"Speicher-Basisdatei: {path}")

    def set_split_progress_max(self, maximum: int):
        self.split_progress["maximum"] = maximum
        self.split_progress["value"] = 0
        self.split_current_steps = 0
        self.split_total_steps = maximum

    def increment_split_progress(self):
        self.split_current_steps += 1
        self.root.after(0, self.update_split_progress_ui)

    def update_split_progress_ui(self):
        self.split_progress["value"] = self.split_current_steps
        if self.split_total_steps > 0:
            percent = int((self.split_current_steps / self.split_total_steps) * 100)
            self.split_status_var.set(f"Verarbeite... {percent}%")

    def start_split_thread(self):
        threading.Thread(target=self.run_split, daemon=True).start()

    def _split_with_pypdf(self, input_pdf: str, output_base: str, ranges: Iterable[tuple[int, int, str]], total_pages: int) -> list[str]:
        reader = PdfReader(input_pdf)
        if not try_decrypt_pypdf(reader, self.access_options()):
            raise ValueError("PDF konnte mit pypdf nicht entsperrt werden.")

        created_files: list[str] = []
        for output_number, (start_index, end_index, label) in enumerate(ranges, start=1):
            output_path = make_numbered_pdf_path(output_base, output_number)
            self.root.after(0, lambda n=output_number, l=label: self.log_split(f"Erstelle Datei {n}: {l}"))
            write_pdf_range_pypdf(reader, start_index, end_index, output_path, self.increment_split_progress)
            created_files.append(output_path)
            self.root.after(0, lambda p=output_path: self.log_split(f"Erstellt: {p}"))
        return created_files

    def _split_with_fitz(self, input_pdf: str, output_base: str, ranges: Iterable[tuple[int, int, str]]) -> list[str]:
        created_files: list[str] = []
        for output_number, (start_index, end_index, label) in enumerate(ranges, start=1):
            output_path = make_numbered_pdf_path(output_base, output_number)
            self.root.after(0, lambda n=output_number, l=label: self.log_split(f"Fallback erstellt Datei {n}: {l}"))
            write_pdf_range_fitz(input_pdf, self.access_options(), start_index, end_index, output_path, self.increment_split_progress)
            created_files.append(output_path)
            self.root.after(0, lambda p=output_path: self.log_split(f"Erstellt: {p}"))
        return created_files

    def run_split(self):
        try:
            self.root.after(0, lambda: self.split_start_button.config(state="disabled"))
            self.root.after(0, lambda: self.split_status_var.set("Starte..."))

            input_pdf = self.input_pdf_var.get().strip()
            output_base = self.output_base_var.get().strip()
            split_text = self.split_pages_var.get().strip()

            if not input_pdf or not os.path.isfile(input_pdf):
                raise ValueError("Bitte zuerst eine gültige PDF-Datei auswählen.")
            if not output_base:
                raise ValueError("Bitte eine Speicher-Basisdatei wählen.")
            output_folder = os.path.dirname(output_base)
            if output_folder and not os.path.isdir(output_folder):
                raise ValueError("Der Speicherordner existiert nicht.")

            # Seitenanzahl möglichst über pypdf, fallback über fitz.
            try:
                reader_probe = PdfReader(input_pdf)
                if not try_decrypt_pypdf(reader_probe, self.access_options()):
                    raise ValueError("pypdf konnte nicht öffnen")
                total_pages = len(reader_probe.pages)
            except Exception:
                doc = open_fitz_document(input_pdf, self.access_options())
                total_pages = doc.page_count
                doc.close()

            if total_pages < 2:
                raise ValueError("Die PDF muss mindestens 2 Seiten haben.")

            split_pages = parse_split_pages(split_text, total_pages)
            ranges = build_ranges(split_pages, total_pages)

            self.root.after(0, lambda: self.set_split_progress_max(total_pages))
            self.root.after(0, lambda: self.log_split(""))
            self.root.after(0, lambda: self.log_split("Starte Splitting..."))
            self.root.after(0, lambda: self.log_split(f"Seitenanzahl: {total_pages}"))
            self.root.after(0, lambda: self.log_split(f"Split-Punkte: {', '.join(map(str, split_pages))}"))
            self.root.after(0, lambda: self.log_split(f"Anzahl Ausgabedateien: {len(ranges)}"))

            try:
                created_files = self._split_with_pypdf(input_pdf, output_base, ranges, total_pages)
            except Exception as pypdf_error:
                if not self.use_fitz_split_fallback_var.get():
                    raise
                self.root.after(0, lambda e=pypdf_error: self.log_split(f"pypdf fehlgeschlagen, versuche PyMuPDF-Fallback: {e}"))
                self.root.after(0, lambda: self.set_split_progress_max(total_pages))
                created_files = self._split_with_fitz(input_pdf, output_base, ranges)

            self.root.after(0, lambda: self.split_status_var.set("Fertig."))
            self.root.after(0, lambda: self.log_split("Fertig."))
            self.root.after(0, lambda: messagebox.showinfo("Fertig", f"PDF-Splitting abgeschlossen.\n\nErstellte Dateien: {len(created_files)}"))

        except Exception as e:
            self.root.after(0, lambda: self.split_status_var.set("Fehler."))
            self.root.after(0, lambda err=e: self.log_split(f"FEHLER: {err}"))
            self.root.after(0, lambda err=e: messagebox.showerror("Fehler", str(err)))
        finally:
            self.root.after(0, lambda: self.split_start_button.config(state="normal"))

    # ------------------------------------------------------------
    # Bild-Export Tab Aktionen
    # ------------------------------------------------------------

    def select_export_mode(self, mode: str):
        self.export_current_var.set(mode == "current")
        self.export_range_var.set(mode == "range")
        self.export_all_var.set(mode == "all")

    def get_export_mode(self) -> str:
        if self.export_current_var.get():
            return "current"
        if self.export_range_var.get():
            return "range"
        if self.export_all_var.get():
            return "all"
        raise ValueError("Bitte auswählen: Aktuelle Seite, Seite X bis X oder Alles.")

    def select_image_output_folder(self):
        folder = filedialog.askdirectory(title="Speicherordner wählen")
        if folder:
            self.image_output_folder_var.set(folder)
            self.log_image(f"Speicherordner: {folder}")

    def set_image_progress_max(self, maximum: int):
        self.image_progress["maximum"] = maximum
        self.image_progress["value"] = 0
        self.image_current_steps = 0
        self.image_total_steps = maximum

    def increment_image_progress(self):
        self.image_current_steps += 1
        self.root.after(0, self.update_image_progress_ui)

    def update_image_progress_ui(self):
        self.image_progress["value"] = self.image_current_steps
        if self.image_total_steps > 0:
            percent = int((self.image_current_steps / self.image_total_steps) * 100)
            self.image_status_var.set(f"Exportiere... {percent}%")

    def start_image_export_thread(self):
        threading.Thread(target=self.run_image_export, daemon=True).start()

    def validate_quality_value(self, fmt: str) -> int:
        fmt = fmt.upper()
        if fmt == "PNG":
            return parse_int_in_range(self.quality_var.get(), "PNG-Kompression", 0, 9)
        if fmt == "JPG":
            return parse_int_in_range(self.quality_var.get(), "JPG-Qualität", 1, 100)
        if fmt == "WEBP":
            return parse_int_in_range(self.quality_var.get(), "WEBP-Qualität", 0, 100)
        if fmt == "GIF":
            return parse_int_in_range(self.quality_var.get(), "GIF-Farben", 2, 256)
        if fmt == "TIFF":
            return parse_int_in_range(self.quality_var.get(), "TIFF-JPEG-Qualität", 1, 100)
        raise ValueError("Nicht unterstütztes Speicherformat.")

    def run_image_export(self):
        try:
            self.root.after(0, lambda: self.image_start_button.config(state="disabled"))
            self.root.after(0, lambda: self.image_status_var.set("Starte..."))

            input_pdf = self.input_pdf_var.get().strip()
            output_folder = self.image_output_folder_var.get().strip()
            prefix = self.image_prefix_var.get().strip()
            dpi = parse_int_in_range(self.image_dpi_var.get(), "DPI", 30, 1200)
            file_type = self.image_format_var.get().strip().upper()
            quality_value = self.validate_quality_value(file_type)
            tiff_compression = self.tiff_compression_var.get().strip()
            mode = self.get_export_mode()

            if not input_pdf or not os.path.isfile(input_pdf):
                raise ValueError("Bitte zuerst eine gültige PDF-Datei auswählen.")
            if not output_folder or not os.path.isdir(output_folder):
                raise ValueError("Bitte einen gültigen Speicherordner wählen.")
            if file_type not in SUPPORTED_IMAGE_FORMATS:
                raise ValueError("Nicht unterstütztes Speicherformat.")

            ext_map = {"PNG": "png", "JPG": "jpg", "TIFF": "tiff", "GIF": "gif", "WEBP": "webp"}
            ext = ext_map[file_type]

            doc = open_fitz_document(input_pdf, self.access_options())
            total_pages = doc.page_count
            if total_pages < 1:
                raise ValueError("Die PDF enthält keine Seiten.")

            pages_to_export = parse_export_pages(
                total_pages=total_pages,
                mode=mode,
                current_page_text=self.current_page_var.get(),
                range_start_text=self.range_start_var.get(),
                range_end_text=self.range_end_var.get(),
            )

            self.root.after(0, lambda: self.set_image_progress_max(len(pages_to_export)))
            self.root.after(0, lambda: self.log_image(""))
            self.root.after(0, lambda: self.log_image("Starte Bildexport..."))
            self.root.after(0, lambda: self.log_image(f"Seitenanzahl PDF: {total_pages}"))
            self.root.after(0, lambda: self.log_image(f"DPI: {dpi}"))
            self.root.after(0, lambda: self.log_image(f"Format: {file_type}"))
            self.root.after(0, lambda: self.log_image(f"Qualität/Kompression: {quality_value}"))
            if file_type == "TIFF":
                self.root.after(0, lambda: self.log_image(f"TIFF-Kompression: {tiff_compression}"))
            self.root.after(0, lambda: self.log_image(f"Zu exportierende Seiten: {pages_to_export}"))

            created_files: list[str] = []
            for seq_number, page_number in enumerate(pages_to_export, start=1):
                output_path = make_image_output_path(output_folder, prefix, page_number, seq_number, ext)
                self.root.after(0, lambda p=page_number: self.log_image(f"Exportiere Seite {p}..."))
                image = render_pdf_page_to_image(doc, page_number, dpi)
                save_image(image, output_path, file_type, quality_value, tiff_compression)
                created_files.append(output_path)
                self.increment_image_progress()
                self.root.after(0, lambda p=output_path: self.log_image(f"Erstellt: {p}"))

            doc.close()
            self.root.after(0, lambda: self.image_status_var.set("Fertig."))
            self.root.after(0, lambda: self.log_image("Fertig."))
            self.root.after(0, lambda: messagebox.showinfo("Fertig", f"Bildexport abgeschlossen.\n\nErstellte Dateien: {len(created_files)}"))

        except Exception as e:
            self.root.after(0, lambda: self.image_status_var.set("Fehler."))
            self.root.after(0, lambda err=e: self.log_image(f"FEHLER: {err}"))
            self.root.after(0, lambda err=e: messagebox.showerror("Fehler", str(err)))
        finally:
            self.root.after(0, lambda: self.image_start_button.config(state="normal"))


if __name__ == "__main__":
    root = tk.Tk()
    app = PdfToolApp(root)
    root.mainloop()
