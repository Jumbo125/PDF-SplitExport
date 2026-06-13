#!/usr/bin/env bash
set -euo pipefail

# PDF-SplitExport Linux Onefile Build
# Author: Andreas Rottmann
# Version: 1.0.0
# License: AGPL-3.0-or-later
#
# Hinweise gegen typische False-Positive-/Build-Probleme:
# - frische virtuelle Umgebung verwenden
# - KEIN UPX verwenden (--noupx)
# - keine obskuren Packer/Protector verwenden
# - Abhaengigkeiten aus serioesen Quellen installieren
# - Linux-Builds immer direkt unter Linux erzeugen
#
# Hinweis:
# - --version-file ist Windows-spezifisch und wird hier deshalb nicht verwendet
# - Assets werden wie im Windows-Build mit eingebunden

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
else
    echo
    echo "Build fehlgeschlagen: Kein Python-Interpreter gefunden."
    echo "Bitte python3 oder python installieren."
    exit 1
fi

"$PYTHON_BIN" -m pip install --upgrade pip
"$PYTHON_BIN" -m pip install -r requirements.txt

rm -rf build_pyinstaller
rm -f dist/PDF-SplitExport

"$PYTHON_BIN" -m PyInstaller \
  --noconfirm \
  --clean \
  --onefile \
  --windowed \
  --noupx \
  --name PDF-SplitExport \
  --add-data "assets:assets" \
  --workpath build_pyinstaller \
  pdf_tool_ui.py

echo
echo "Fertig: dist/PDF-SplitExport"
