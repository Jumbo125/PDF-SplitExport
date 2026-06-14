<p align="center">
  <img src="assets/app.ico" width="72" alt="PDF-SplitExport Icon">
</p>

<h1 align="center">PDF-SplitExport</h1>

<p align="center">
  <img alt="Version" src="https://img.shields.io/badge/version-2.0.0-blue">
  <img alt="Python" src="https://img.shields.io/badge/python-3.10%2B-blue">
  <img alt="License" src="https://img.shields.io/badge/license-AGPL--3.0--or--later-green">
  <img alt="Platform" src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS-lightgrey">
</p>

**Author:** Andreas Rottmann (mit AI-Unterstützung)  
**License:** AGPL-3.0-or-later  
**Version:** 2.0.0

---

## Deutsch

PDF-SplitExport 2.0 ist eine lokale Tkinter-App für PDF-Aufteilung, PDF-Extraktion, PDF-Merger und Bildexport aus PDF-Seiten.

### Release-Highlights 2.0

- Neuer PDF-Modus mit `Splitter`, `Extraktor` und `Merger`
- Extraktor mit Einzelbereich oder mehreren getrennten Ausgaben
- Merger mit frei definierbarer Seitenreihenfolge
- Live-Vorschau und direkte Eingabeprüfung im PDF-Bereich
- Sichtbare Seitenanzahl direkt in der Oberfläche
- Weiterhin kein OCR und keine Bildumwandlung bei PDF-zu-PDF-Aktionen

### Funktionen

- `Splitter`: `10,25` erzeugt `1-10`, `11-25`, `26-Ende`
- `Extraktor`: `7` oder `7-12` erzeugt genau eine neue PDF
- `Extraktor`: `2,5-7,10` erzeugt mehrere einzelne PDFs
- `Merger`: `3+5+8` oder `3+5-7+10` erzeugt eine neue PDF in genau dieser Reihenfolge
- PDF-zu-PDF ohne OCR und ohne Rendern
- Markierbarer Text bleibt erhalten, wenn die Original-PDF echten Text enthält
- Bildexport als `PNG`, `JPG`, `TIFF`, `GIF`, `WEBP`
- Frei einstellbare DPI
- Formatabhängige Qualität und Kompression
- Passwort-Eingabe für geschützte PDFs
- Optionaler Versuch ohne Passwort bei leerem User-Passwort oder reinen Berechtigungs-/Owner-Flags
- Dynamischer Dateiname für Bildexport
- Windows-Build mit Versionsinfo und Icon
- macOS-Build per GitHub Actions

### Installation

```bash
pip install -r requirements.txt
python pdf_tool_ui.py
```

### PDF-Modi

#### Splitter

```text
10,25
```

Ergebnis:

```text
Datei 1 = Seite 1 bis 10
Datei 2 = Seite 11 bis 25
Datei 3 = Seite 26 bis Ende
```

#### Extraktor

Eine Datei:

```text
7
7-12
```

Mehrere Dateien:

```text
2,5-7,10
```

Ergebnis:

```text
Datei 1 = Seite 2
Datei 2 = Seite 5 bis 7
Datei 3 = Seite 10
```

#### Merger

```text
3+5+8
3+5-7+10
```

Ergebnis:

```text
Eine neue PDF mit genau dieser Seitenreihenfolge
```

### Bildexport

Unterstützte Formate:

```text
PNG, JPG, TIFF, GIF, WEBP
```

Seitenauswahl:

```text
Aktuelle Seite
Seite X bis X
Alles exportieren
```

Dateinamens-Prefix:

```text
scan
scan_{page0}
export_{n0}_p{page0}
```

Platzhalter:

```text
{page}  = PDF-Seite, z. B. 7
{page0} = PDF-Seite dreistellig, z. B. 007
{n}     = laufende Nummer, z. B. 1
{n0}    = laufende Nummer dreistellig, z. B. 001
```

### Qualität / Kompression

```text
PNG  = Kompression 0-9
JPG  = Qualität 1-100
WEBP = Qualität 0-100
GIF  = Farben 2-256
TIFF = Kompression: tiff_deflate, lzw, jpeg oder none
```

### Geschützte PDFs

Die App knackt keine Passwörter und umgeht keine echte Verschlüsselung.  
Der Modus `ohne Passwort versuchen` hilft nur, wenn die Datei technisch ohne echtes User-Passwort geöffnet werden kann.

### Build

Windows:

```cmd
build\build_windows_onefile.cmd
```

Linux:

```bash
build/build_linux_onefile.sh
```

macOS Workflow:

```text
.github/workflows/build-macos.yml
```

---

## English

PDF-SplitExport 2.0 is a local Tkinter app for PDF splitting, PDF extraction, PDF merging, and exporting PDF pages as images.

### 2.0 Release Highlights

- New PDF mode section with `Splitter`, `Extractor`, and `Merger`
- Extractor supports single ranges and multiple separate outputs
- Merger supports freely defined page order
- Live preview and inline validation in the PDF input area
- Visible page count directly in the UI
- Still no OCR and no rendering for PDF-to-PDF actions

### Features

- `Splitter`: `10,25` creates `1-10`, `11-25`, `26-end`
- `Extractor`: `7` or `7-12` creates exactly one new PDF
- `Extractor`: `2,5-7,10` creates multiple separate PDF files
- `Merger`: `3+5+8` or `3+5-7+10` creates one PDF in exactly that order
- PDF-to-PDF processing without OCR and without page rendering
- Selectable text remains intact if the source PDF contains real text
- Image export as `PNG`, `JPG`, `TIFF`, `GIF`, `WEBP`
- Configurable DPI
- Format-specific quality and compression
- Password input for protected PDFs
- Optional open attempt without password for empty user passwords or permission/owner-only protection
- Dynamic output naming for image export
- Windows build with icon and version metadata
- macOS build via GitHub Actions

### Installation

```bash
pip install -r requirements.txt
python pdf_tool_ui.py
```

### PDF Modes

#### Splitter

```text
10,25
```

Result:

```text
File 1 = page 1 to 10
File 2 = page 11 to 25
File 3 = page 26 to end
```

#### Extractor

Single output:

```text
7
7-12
```

Multiple outputs:

```text
2,5-7,10
```

Result:

```text
File 1 = page 2
File 2 = page 5 to 7
File 3 = page 10
```

#### Merger

```text
3+5+8
3+5-7+10
```

Result:

```text
One new PDF with exactly that page order
```

### Image Export

Supported formats:

```text
PNG, JPG, TIFF, GIF, WEBP
```

Page selection:

```text
Current page
Page X to X
Export all
```

Filename prefix:

```text
scan
scan_{page0}
export_{n0}_p{page0}
```

Placeholders:

```text
{page}  = PDF page, e.g. 7
{page0} = zero-padded PDF page, e.g. 007
{n}     = running number, e.g. 1
{n0}    = zero-padded running number, e.g. 001
```

### Quality / Compression

```text
PNG  = compression 0-9
JPG  = quality 1-100
WEBP = quality 0-100
GIF  = colors 2-256
TIFF = compression: tiff_deflate, lzw, jpeg, or none
```

### Protected PDFs

The app does not crack passwords and does not bypass real encryption.  
The `try without password` mode only helps when the file is technically accessible without a real user password.

### Build

Windows:

```cmd
build\build_windows_onefile.cmd
```

Linux:

```bash
build/build_linux_onefile.sh
```

macOS workflow:

```text
.github/workflows/build-macos.yml
```
