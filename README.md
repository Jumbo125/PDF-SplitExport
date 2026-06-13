<p align="center">
  <img src="assets/app.ico" width="72" alt="PDF-SplitExport Icon">
</p>

<h1 align="center">PDF-SplitExport</h1>

<p align="center">
  <img alt="Version" src="https://img.shields.io/badge/version-1.0.0-blue">
  <img alt="Python" src="https://img.shields.io/badge/python-3.10%2B-blue">
  <img alt="License" src="https://img.shields.io/badge/license-AGPL--3.0--or--later-green">
  <img alt="Platform" src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS-lightgrey">
</p>

**Author:** Andreas Rottmann (mit AI-Unterstützung)  
**License:** AGPL-3.0-or-later  
**Version:** 1.0.0

Dieses Projekt wurde von Andreas Rottmann mit AI-Unterstützung erstellt.

---

## Deutsch

PDF-SplitExport ist eine kleine lokale Tkinter-App zum Splitten von PDFs und zum Exportieren einzelner PDF-Seiten als Bild.

### Funktionen

- PDF in fortlaufende Bereiche splitten
- Kein OCR und keine Bildumwandlung beim PDF-Split
- Markierbarer Text bleibt erhalten, wenn die Original-PDF echten Text enthält
- Seiten als PNG, JPG, TIFF, GIF oder WEBP exportieren
- DPI frei einstellbar
- Formatabhängige Qualität/Kompression
- Passwort-Eingabe für geschützte PDFs
- Optionaler Versuch ohne Passwort bei PDFs mit leerem User-Passwort oder reinen Berechtigungs-/Owner-Flags
- Dynamischer Prefix für Bilddateien
- Windows-Onefile-Build mit Icon und Versionsinfo
- macOS-Build über GitHub Actions

### Installation

```bash
pip install -r requirements.txt
```

Start:

```bash
python pdf_tool_ui.py
```

### PDF splitten

Beispiel:

```text
Split-Seiten: 10,25
```

Ergebnis:

```text
output_1.pdf = Seite 1 bis 10
output_2.pdf = Seite 11 bis 25
output_3.pdf = Seite 26 bis Ende
```

Der PDF-Split kopiert echte PDF-Seiten. Es wird nichts gerendert und kein OCR durchgeführt.

### Seiten als Bild exportieren

Unterstützte Formate:

```text
PNG, JPG, TIFF, GIF, WEBP
```

Seiten-Auswahl:

```text
Aktuelle Seite
Seite X bis X
Alles exportieren
```

Dynamischer Prefix:

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

### Passwortgeschützte PDFs

Du kannst ein Passwort eingeben. Zusätzlich kann die App versuchen, eine geschützte PDF ohne Passwort zu öffnen, wenn die Datei technisch ohne User-Passwort zugänglich ist.

Wichtig: Die App knackt keine Passwörter und umgeht keine echte Verschlüsselung. Der Modus hilft nur bei PDFs mit leerem User-Passwort oder reinen Berechtigungs-/Owner-Flags.

### Windows EXE bauen

```cmd
build\build_windows_onefile.cmd
```

Ausgabe:

```text
dist\PDFTool.exe
```

Bei Onefile-Builds kann es gelegentlich Antivirus-False-Positives geben. Das Build-Script verwendet `--noupx`, ein eigenes Icon und eine Versionsinfo. Für öffentliche Verteilung ist Code-Signing empfehlenswert.

### macOS Build über GitHub Actions

Die Workflow-Datei liegt hier:

```text
.github/workflows/build-macos.yml
```

Nach dem Workflow findest du das gebaute Artefakt im GitHub-Actions-Run.

---

## English

PDF-SplitExport is a small local Tkinter app for splitting PDFs and exporting PDF pages as images.

### Features

- Split PDFs into continuous ranges
- No OCR and no image rendering during PDF splitting
- Selectable text is preserved if the source PDF contains real text
- Export pages as PNG, JPG, TIFF, GIF, or WEBP
- Configurable DPI
- Format-specific quality/compression settings
- Password input for protected PDFs
- Optional attempt to open protected PDFs without a password when the file is technically accessible without a user password
- Dynamic image filename prefix
- Windows onefile build with icon and version resource
- macOS build via GitHub Actions

### Installation

```bash
pip install -r requirements.txt
```

Run:

```bash
python pdf_tool_ui.py
```

### Split PDFs

Example:

```text
Split pages: 10,25
```

Result:

```text
output_1.pdf = page 1 to 10
output_2.pdf = page 11 to 25
output_3.pdf = page 26 to end
```

The split operation copies real PDF pages. It does not render pages and does not perform OCR.

### Export pages as images

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

Dynamic prefix examples:

```text
scan
scan_{page0}
export_{n0}_p{page0}
```

Placeholders:

```text
{page}  = PDF page number, e.g. 7
{page0} = zero-padded PDF page number, e.g. 007
{n}     = running number, e.g. 1
{n0}    = zero-padded running number, e.g. 001
```

### Quality / compression

```text
PNG  = compression level 0-9
JPG  = quality 1-100
WEBP = quality 0-100
GIF  = colors 2-256
TIFF = compression: tiff_deflate, lzw, jpeg, or none
```

### Protected PDFs

You can enter a PDF password. The app can also try to open a protected PDF without a password if the file is technically accessible without a user password.

Important: The app does not crack passwords and does not bypass real encryption. This mode only helps with empty user passwords or permission/owner-flag protected PDFs.

### Build Windows EXE

```cmd
build\build_windows_onefile.cmd
```

Output:

```text
dist\PDFTool.exe
```

Onefile builds may occasionally trigger antivirus false positives. The build script uses `--noupx`, a custom icon, and Windows version metadata. For public distribution, code signing is recommended.

### Build macOS via GitHub Actions

Workflow file:

```text
.github/workflows/build-macos.yml
```

The built artifact is available from the GitHub Actions run.
