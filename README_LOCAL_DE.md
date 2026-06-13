# PDF-SplitExport 1.0 - lokale Anleitung

**Author:** Andreas Rottmann  
**License:** AGPL-3.0-or-later

Dieses kleine Tkinter-Tool hat zwei Hauptfunktionen:

1. **PDF splitten** ohne OCR und ohne Bildumwandlung
2. **PDF-Seiten als Bild exportieren** mit DPI, Format und Qualität/Kompression

## Installation für Python

```bash
pip install -r requirements.txt
```

Start:

```bash
python pdf_tool_ui.py
```

## Reiter 1: PDF splitten

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

Die PDF wird nicht gerendert. Die Seiten werden als echte PDF-Seiten kopiert. Wenn der Text in der Original-PDF markierbar war, bleibt er normalerweise markierbar.

## Reiter 2: Seiten als Bild exportieren

Unterstützte Formate:

- PNG
- JPG
- TIFF
- GIF
- WEBP

Auswahlmöglichkeiten:

- Aktuelle Seite
- Seite X bis X
- Alles exportieren

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

## Qualität / Kompression

Je nach Format wird die Eingabe anders interpretiert:

```text
PNG  = Kompression 0-9
JPG  = Qualität 1-100
WEBP = Qualität 0-100
GIF  = Farben 2-256
TIFF = Qualität nur bei TIFF-Kompression jpeg relevant
```

## Passwortgeschützte PDFs

Du kannst ein PDF-Passwort eingeben.

Zusätzlich gibt es die Checkbox:

```text
Geschützte PDF ohne Passwort versuchen, wenn technisch möglich / leeres User-Passwort
```

Das knackt keine Passwörter. Es hilft nur bei PDFs, die zwar Berechtigungs-/Owner-Schutz oder ein leeres User-Passwort haben, technisch aber ohne Passwort geöffnet werden können.

## Windows EXE bauen

Im Projektordner ausführen:

```cmd
build\build_windows_onefile.cmd
```

Ausgabe:

```text
dist\PDFTool.exe
```

Hinweis: Bei PyInstaller-Onefile kann es gelegentlich zu Antivirus-False-Positives kommen. Das Script verwendet deshalb `--noupx`, eine klare Versionsinfo und ein Icon. Für Veröffentlichung ist Code-Signing am besten.
