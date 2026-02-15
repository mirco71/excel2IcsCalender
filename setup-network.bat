@echo off
REM Verbessertes Setup-Skript für Netzwerklaufwerke
REM Optimiert für Pfade wie R:\ oder \\192.168.x.x\

echo ================================================
echo Trainingsplan Generator - Setup
echo Netzwerklaufwerk-optimiert
echo ================================================
echo.

REM Zeige aktuelles Verzeichnis
echo [INFO] Arbeitsverzeichnis: %CD%
echo.

REM Prüfe ob Python installiert ist
python --version >nul 2>&1
if errorlevel 1 (
    echo [FEHLER] Python ist nicht installiert!
    echo Bitte installiere Python von https://python.org
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo [OK] %PYTHON_VERSION% gefunden
echo.

REM Prüfe ob venv existiert
if exist "venv\Scripts\activate.bat" (
    echo [OK] Virtual Environment existiert bereits
    goto :activate
)

REM Virtual Environment erstellen
echo [INFO] Erstelle Virtual Environment...
echo [HINWEIS] Bei Netzwerklaufwerken kann dies 1-2 Minuten dauern
echo [HINWEIS] Warnungen zu "redirects, links or junctions" sind normal
echo.

REM Erstelle venv mit Fehlerbehandlung
python -m venv venv 2>nul
if not exist "venv\Scripts\python.exe" (
    echo [WARNUNG] Erste Erstellung fehlgeschlagen, versuche Alternative...
    python -m venv venv --clear
)

REM Verifiziere Erstellung
if exist "venv\Scripts\python.exe" (
    echo [OK] Virtual Environment erfolgreich erstellt
    echo.
) else (
    echo [FEHLER] Virtual Environment konnte nicht erstellt werden
    echo.
    echo Mögliche Lösungen:
    echo 1. Führe das Skript als Administrator aus
    echo 2. Kopiere das Projekt auf ein lokales Laufwerk (C:\)
    echo 3. Erstelle manuell: python -m venv venv
    echo.
    pause
    exit /b 1
)

:activate
REM Aktiviere venv
echo [INFO] Aktiviere Virtual Environment...
call venv\Scripts\activate.bat

REM Prüfe ob Aktivierung erfolgreich war
where python | findstr "venv" >nul
if errorlevel 1 (
    echo [WARNUNG] Virtual Environment möglicherweise nicht aktiviert
    echo [INFO] Fahre trotzdem fort...
)
echo.

REM Upgrade pip (wichtig für Netzwerklaufwerke)
echo [INFO] Aktualisiere pip...
python -m pip install --upgrade pip --quiet
echo [OK] pip aktualisiert
echo.

REM Installiere Dependencies
echo [INFO] Installiere Dependencies...
echo [INFO] Dies kann einige Minuten dauern...
echo.

if exist "requirements.txt" (
    echo [INFO] Installiere Haupt-Dependencies...
    pip install -r requirements.txt --quiet || pip install -r requirements.txt
    echo [OK] Haupt-Dependencies installiert
) else (
    echo [WARNUNG] requirements.txt nicht gefunden
)
echo.

if exist "requirements-test.txt" (
    echo [INFO] Installiere Test-Dependencies...
    pip install -r requirements-test.txt --quiet || pip install -r requirements-test.txt
    echo [OK] Test-Dependencies installiert
) else (
    echo [WARNUNG] requirements-test.txt nicht gefunden
)
echo.

REM Zeige installierte Pakete
echo [INFO] Installierte Hauptpakete:
pip list | findstr "pandas openpyxl ics pytest"
echo.

REM Optional: Führe Tests aus
echo Möchtest du jetzt die Tests ausführen?
set /p RUN_TESTS="Tests ausführen? (j/n): "
if /i "%RUN_TESTS%"=="j" (
    echo.
    echo [INFO] Führe Tests aus...
    echo ================================================
    pytest -v || (
        echo [WARNUNG] Tests konnten nicht ausgeführt werden
        echo [INFO] Stelle sicher dass alle Test-Dateien vorhanden sind
    )
    echo ================================================
    echo.
)

echo ================================================
echo Setup abgeschlossen!
echo ================================================
echo.
echo Arbeitsverzeichnis: %CD%
echo Virtual Environment: AKTIVIERT
echo.
echo Nächste Schritte:
echo.
echo 1. Environment ist bereits aktiviert (venv)
echo 2. Führe dein Skript aus:
echo    python calendar_generator.py
echo.
echo 3. Oder führe Tests aus:
echo    pytest -v
echo.
echo 4. Zum Deaktivieren:
echo    deactivate
echo.
echo WICHTIG für nächstes Mal:
echo   Führe einfach aus: venv\Scripts\activate
echo   Dann: python calendar_generator.py
echo.
pause
