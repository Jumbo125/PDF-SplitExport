@echo off
setlocal

REM PDF-SplitExport Windows Onefile Build
REM Author: Andreas Rottmann
REM Version: 1.0.0
REM License: AGPL-3.0-or-later
REM
REM Hinweise gegen typische False-Positive-Probleme:
REM - frische virtuelle Umgebung verwenden
REM - KEIN UPX verwenden (--noupx)
REM - keine obskuren Packer/Protector verwenden
REM - Abhängigkeiten aus seriösen Quellen installieren
REM - für Veröffentlichung idealerweise Code-Signing verwenden
REM - falls Antivirus trotzdem anschlägt: Datei beim AV-Hersteller als False Positive einreichen

cd /d "%~dp0\.."

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

rmdir /s /q build_pyinstaller 2>nul
if exist dist\PDF-SplitExport.exe del /q dist\PDF-SplitExport.exe

python -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onefile ^
  --windowed ^
  --noupx ^
  --name PDF-SplitExport ^
  --icon assets\app.ico ^
  --version-file build\version_info.txt ^
  --add-data "assets;assets" ^
  --workpath build_pyinstaller ^
  pdf_tool_ui.py

if errorlevel 1 (
  echo.
  echo Build fehlgeschlagen.
  pause
  exit /b 1
)

echo.
echo Fertig: dist\PDF-SplitExport.exe
echo.
pause
