# PDF-SplitExport 2.0.0 - lokale Anleitung

**Author:** Andreas Rottmann  
**License:** AGPL-3.0-or-later

PDF-SplitExport 2.0 hat jetzt vier klare Hauptfunktionen:

1. `Splitter` für fortlaufende PDF-Bereiche
2. `Extraktor` für einzelne Seiten, Bereiche oder mehrere getrennte Ausgaben
3. `Merger` für frei kombinierte Seitenreihenfolgen
4. `Bildexport` für PDF-Seiten als PNG, JPG, TIFF, GIF oder WEBP

## Installation

```bash
pip install -r requirements.txt
python pdf_tool_ui.py
```

## PDF-Bereich

Im PDF-Reiter gibt es drei Modi:

### 1. Splitter

Eingabe:

```text
10,25
```

Ergebnis:

```text
Datei 1 = Seite 1 bis 10
Datei 2 = Seite 11 bis 25
Datei 3 = Seite 26 bis Ende
```

### 2. Extraktor

Eine einzelne Ausgabedatei:

```text
7
7-12
```

Mehrere Ausgabedateien:

```text
2,5-7,10
```

Ergebnis:

```text
Datei 1 = Seite 2
Datei 2 = Seite 5 bis 7
Datei 3 = Seite 10
```

Wichtig: Beim Extraktor bedeutet Komma getrennte Einzelausgaben. Das ist absichtlich anders als beim Merger.

### 3. Merger

Eingabe:

```text
3+5+8
3+5-7+10
```

Ergebnis:

```text
Eine neue PDF mit genau dieser Reihenfolge
```

## Live-Hilfe im PDF-Reiter

Die Oberfläche zeigt jetzt direkt:

- die Seitenanzahl der geladenen PDF
- eine Live-Vorschau der Eingabe
- eine direkte Validierung, falls das Format ungültig ist

## Bildexport

Unterstützte Formate:

- PNG
- JPG
- TIFF
- GIF
- WEBP

Seitenauswahl:

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

```text
PNG  = Kompression 0-9
JPG  = Qualität 1-100
WEBP = Qualität 0-100
GIF  = Farben 2-256
TIFF = Kompression: tiff_deflate, lzw, jpeg oder none
```

## Passwortgeschützte PDFs

Du kannst ein PDF-Passwort eingeben. Zusätzlich kann die App versuchen, eine geschützte PDF ohne Passwort zu öffnen, wenn sie technisch ohne echtes User-Passwort zugänglich ist.

Die App knackt keine Passwörter und umgeht keine echte Verschlüsselung.

## Build

Windows:

```cmd
build\build_windows_onefile.cmd
```

Linux:

```bash
build/build_linux_onefile.sh
```

macOS:

```text
.github/workflows/build-macos.yml
```
