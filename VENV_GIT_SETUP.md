# Virtual Environment Setup & Git Integration

## 🎯 Ziel
Ein sauberes, isoliertes Python-Environment erstellen, das mit Git versioniert werden kann.

## ⚠️ WICHTIG: Was gehört NICHT in Git?

### ❌ NICHT einchecken:
- `venv/` oder `.venv/` Ordner (zu groß, plattformabhängig)
- `__pycache__/` Ordner
- `.pyc` Dateien
- Temporäre Dateien
- Lokale IDE-Einstellungen

### ✅ Einchecken:
- `requirements.txt` - Liste aller Dependencies
- `requirements-test.txt` - Test-Dependencies
- `.python-version` - Python-Version
- `pyproject.toml` - Projekt-Konfiguration
- `.gitignore` - Was nicht eingecheckt werden soll

## 📋 Schritt-für-Schritt Anleitung

### 1. Virtual Environment erstellen

**Windows (PowerShell/CMD):**
```powershell
# Ins Projektverzeichnis wechseln
cd C:\Pfad\zu\deinem\Projekt

# Virtual Environment erstellen
python -m venv venv

# Aktivieren
venv\Scripts\activate

# Prüfen ob aktiviert (sollte (venv) vor der Zeile zeigen)
python --version
```

**macOS/Linux:**
```bash
# Ins Projektverzeichnis wechseln
cd /pfad/zu/deinem/projekt

# Virtual Environment erstellen
python3 -m venv venv

# Aktivieren
source venv/bin/activate

# Prüfen ob aktiviert
python --version
```

### 2. Dependencies installieren

```bash
# Haupt-Dependencies
pip install pandas openpyxl ics python-dateutil

# Test-Dependencies
pip install pytest pytest-cov pytest-xdist

# Alle Dependencies in Datei speichern
pip freeze > requirements.txt
```

### 3. Git Repository initialisieren

```bash
# Git initialisieren (falls noch nicht geschehen)
git init

# Git-Konfiguration (einmalig)
git config --global user.name "Dein Name"
git config --global user.email "deine.email@example.com"

# Status prüfen
git status
```

### 4. Erste Commit erstellen

```bash
# Alle Dateien zum Staging hinzufügen
git add .

# Ersten Commit erstellen
git commit -m "Initial commit: Trainingsplan Generator mit Tests"

# Remote Repository verbinden (GitHub)
git remote add origin https://github.com/USERNAME/REPOSITORY.git
git branch -M main
git push -u origin main
```

## 📁 Empfohlene Projektstruktur

```
trainingsplan-generator/
├── .git/                          # Git Ordner (automatisch erstellt)
├── .gitignore                     # ✅ Einchecken
├── .python-version                # ✅ Einchecken
├── README.md                      # ✅ Einchecken
├── requirements.txt               # ✅ Einchecken
├── requirements-test.txt          # ✅ Einchecken
├── pyproject.toml                 # ✅ Einchecken
│
├── .vscode/                       # VS Code Settings
│   ├── settings.json              # ✅ Einchecken (Team-Settings)
│   ├── tasks.json                 # ✅ Einchecken
│   └── extensions.json            # ✅ Einchecken (optional)
│
├── venv/                          # ❌ NICHT einchecken
│   ├── Lib/
│   ├── Scripts/
│   └── ...
│
├── src/                           # Quellcode
│   ├── __init__.py
│   ├── calendar_generator.py     # ✅ Einchecken
│   └── utils.py                   # ✅ Einchecken
│
├── tests/                         # Tests
│   ├── __init__.py
│   ├── test_calendar_generator.py # ✅ Einchecken
│   └── test_utils.py              # ✅ Einchecken
│
├── data/                          # Beispieldaten
│   └── sample_trainingsplan.xlsx  # ⚠️ Optional einchecken
│
├── output/                        # Generierte Dateien
│   ├── calendar_csv/              # ❌ NICHT einchecken
│   └── calendar_ics/              # ❌ NICHT einchecken
│
└── docs/                          # Dokumentation
    └── TEST_SETUP_ANLEITUNG.md    # ✅ Einchecken
```

## 🔧 VS Code Integration

### VS Code erkennt Virtual Environment automatisch

1. **Öffne Command Palette**: `Ctrl+Shift+P` (Windows) oder `Cmd+Shift+P` (Mac)
2. Tippe: "Python: Select Interpreter"
3. Wähle: `./venv/Scripts/python.exe` (Windows) oder `./venv/bin/python` (Mac/Linux)

VS Code zeigt dann unten links das aktive Environment: `Python 3.11.x ('venv')`

### Terminal in VS Code nutzt automatisch das Environment

Nach der Auswahl öffnet jedes neue Terminal automatisch das venv!

## 🚀 Täglicher Workflow

```bash
# 1. Projekt öffnen
cd /pfad/zum/projekt

# 2. Environment aktivieren
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# 3. Arbeiten...
# Code schreiben, Tests ausführen, etc.

# 4. Änderungen committen
git add .
git commit -m "Beschreibung der Änderungen"
git push

# 5. Environment deaktivieren (am Ende)
deactivate
```

## 👥 Für Teammitglieder

Wenn jemand dein Projekt klont:

```bash
# Repository klonen
git clone https://github.com/USERNAME/REPOSITORY.git
cd REPOSITORY

# Virtual Environment erstellen
python -m venv venv

# Environment aktivieren
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Dependencies installieren
pip install -r requirements.txt
pip install -r requirements-test.txt

# Tests ausführen um zu prüfen ob alles funktioniert
pytest -v
```

## 🔄 Dependencies aktualisieren

```bash
# Neue Pakete installieren
pip install neues-paket

# Requirements aktualisieren
pip freeze > requirements.txt

# In Git einchecken
git add requirements.txt
git commit -m "Add neues-paket dependency"
git push
```

## 💡 Best Practices

### 1. Environment-Namen konsistent halten
- ✅ Immer `venv` nutzen
- ✅ Oder projektspezifisch: `.venv-trainingsplan`

### 2. Python-Version dokumentieren
Erstelle `.python-version`:
```
3.11.5
```

### 3. Unterschiedliche Requirements-Dateien
- `requirements.txt` - Produktions-Dependencies
- `requirements-test.txt` - Test-Dependencies
- `requirements-dev.txt` - Entwickler-Tools (optional)

### 4. Lock-Files verwenden (fortgeschritten)
Für reproduzierbare Builds:
```bash
pip install pip-tools
pip-compile requirements.in -o requirements.txt
```

## 🐛 Häufige Probleme & Lösungen

### Problem: "pip: command not found"
**Lösung:**
```bash
python -m pip install --upgrade pip
```

### Problem: Environment aktiviert sich nicht
**Windows:**
```powershell
# PowerShell Execution Policy ändern
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Problem: Falsche Python-Version im venv
**Lösung:**
```bash
# Explizite Python-Version nutzen
python3.11 -m venv venv
```

### Problem: Git verfolgt venv-Ordner
**Lösung:**
```bash
# Aus Git-Tracking entfernen
git rm -r --cached venv/
git commit -m "Remove venv from tracking"
```

## 📊 Environment-Status prüfen

```bash
# Aktives Environment anzeigen
which python     # macOS/Linux
where python     # Windows

# Installierte Pakete anzeigen
pip list

# Paket-Details anzeigen
pip show pandas

# Veraltete Pakete finden
pip list --outdated
```

## 🔐 Sicherheit

### Secrets NIEMALS einchecken!
Erstelle `.env` Datei für sensible Daten:

```env
API_KEY=dein-secret-key
DATABASE_URL=postgresql://...
```

Füge zu `.gitignore` hinzu:
```
.env
*.env
secrets.json
```

Lade Secrets mit `python-dotenv`:
```python
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv('API_KEY')
```

## ✅ Checkliste

Vor dem ersten Push:

- [ ] Virtual Environment erstellt (`venv/`)
- [ ] `.gitignore` konfiguriert
- [ ] `requirements.txt` erstellt
- [ ] Tests laufen erfolgreich (`pytest -v`)
- [ ] README.md erstellt
- [ ] `.python-version` erstellt
- [ ] Keine Secrets im Code
- [ ] VS Code Interpreter ausgewählt

## 🎓 Weiterführende Themen

- **Poetry**: Moderner Python Package Manager
- **Docker**: Container für vollständige Isolation
- **pyenv**: Verwaltung mehrerer Python-Versionen
- **tox**: Tests in mehreren Environments

---

**Fragen?** Öffne ein Issue auf GitHub oder kontaktiere das Team!
