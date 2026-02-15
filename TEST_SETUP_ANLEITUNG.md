# Test-Automatisierung Setup für Trainingsplan-Kalender

## 📋 Übersicht

Diese Anleitung hilft dir, eine vollständige Test-Automatisierung für dein Python-Skript einzurichten.

## 🛠️ Voraussetzungen

- Python 3.10 oder höher
- VS Code installiert
- Git (optional, aber empfohlen)

## 📦 Installation

### 1. Projekt vorbereiten

```bash
# Erstelle eine virtuelle Umgebung
python -m venv venv

# Aktiviere die virtuelle Umgebung
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Installiere Dependencies
pip install -r requirements-test.txt
```

### 2. VS Code Extensions installieren

Empfohlene Extensions:
- **Python** (Microsoft)
- **Python Test Explorer** (Little Fox Team)
- **Coverage Gutters** (ryanluker) - für Code Coverage Visualisierung

```
code --install-extension ms-python.python
code --install-extension littlefoxteam.vscode-python-test-adapter
code --install-extension ryanluker.vscode-coverage-gutters
```

### 3. Projektstruktur anpassen

Benenne dein Hauptskript um:
```
Dein_Skript.py → calendar_generator.py
```

Oder passe die Imports in `test_calendar_generator.py` an.

**Empfohlene Struktur:**
```
projekt/
├── calendar_generator.py      # Dein Hauptskript
├── test_calendar_generator.py # Test-Datei
├── requirements-test.txt       # Test-Dependencies
├── pyproject.toml             # Pytest-Konfiguration
├── .vscode/
│   ├── settings.json          # VS Code Einstellungen
│   └── tasks.json             # Test-Tasks
└── tests/                     # Optional: Alle Tests hier
    └── test_*.py
```

### 4. VS Code Konfiguration

Kopiere die Dateien:
```bash
# Erstelle .vscode Ordner falls nicht vorhanden
mkdir -p .vscode

# Kopiere die Config-Dateien
cp .vscode_settings.json .vscode/settings.json
cp .vscode_tasks.json .vscode/tasks.json
```

## 🚀 Tests ausführen

### Option 1: Kommandozeile

```bash
# Alle Tests ausführen
pytest

# Mit ausführlicher Ausgabe
pytest -v

# Mit Code Coverage
pytest --cov=. --cov-report=html

# Einzelne Test-Datei
pytest test_calendar_generator.py

# Einzelnen Test ausführen
pytest test_calendar_generator.py::TestCleanTimeStr::test_valid_time_string

# Tests parallel ausführen (schneller)
pytest -n auto
```

### Option 2: VS Code Testing Panel

1. Öffne das Testing Panel (Becher-Icon in der Seitenleiste)
2. Klicke auf "Refresh Tests"
3. Alle Tests werden angezeigt
4. Klicke auf ▶️ neben einem Test zum Ausführen
5. Klicke auf 🪲 zum Debuggen eines Tests

### Option 3: VS Code Tasks

Drücke `Ctrl+Shift+P` (Windows/Linux) oder `Cmd+Shift+P` (macOS):
- Wähle "Tasks: Run Task"
- Wähle eine der verfügbaren Tasks:
  - **Run All Tests** - Alle Tests ausführen
  - **Run Tests with Coverage** - Mit Code Coverage
  - **Run Single Test File** - Aktuell geöffnete Datei testen

## 📊 Code Coverage

Nach dem Ausführen mit Coverage:

```bash
# HTML-Report öffnen
open htmlcov/index.html  # macOS
start htmlcov/index.html # Windows
xdg-open htmlcov/index.html # Linux
```

Der Report zeigt:
- Welche Zeilen getestet wurden (grün)
- Welche Zeilen nicht getestet wurden (rot)
- Prozentuale Abdeckung

## 🎯 Test-Strategie

### Unit Tests
Teste einzelne Funktionen isoliert:
- ✅ `clean_time_str()`
- ✅ `is_training_time()`
- ✅ `parse_time_range()`
- ✅ `parse_game()`

### Integration Tests
Teste das Zusammenspiel mehrerer Komponenten:
- Excel-Datei einlesen
- CSV/ICS Dateien erstellen
- U11A/U11B Zusammenführung

### Edge Cases
Teste Randfälle:
- Leere Zellen
- Ungültige Zeitformate
- Sonderzeichen in Namen

## 🔧 Refactoring des Hauptskripts

Um bessere Testbarkeit zu erreichen, strukturiere dein Skript um:

```python
# calendar_generator.py

# ... (alle Hilfsfunktionen bleiben gleich) ...

def process_calendar(excel_file: str, sheet_name: str, 
                     output_dir_csv: Path, output_dir_ics: Path):
    """Hauptlogik in testbarer Funktion"""
    # Deine gesamte Logik hier
    pass

if __name__ == "__main__":
    # Konfiguration
    excel_file = "2025-2026_Trainingsplan Master.xlsx"
    sheet_name = "2026 Master"
    output_dir_csv = Path("calendar_csv")
    output_dir_ics = Path("calendar_ics")
    
    # Ausführen
    process_calendar(excel_file, sheet_name, output_dir_csv, output_dir_ics)
```

## 🔄 Continuous Integration (Optional)

### GitHub Actions

Erstelle `.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        pip install -r requirements-test.txt
    - name: Run tests
      run: |
        pytest --cov=. --cov-report=xml
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## 📝 Best Practices

1. **Teste früh und oft** - Führe Tests bei jeder Änderung aus
2. **Kleine Tests** - Jeder Test sollte eine Sache testen
3. **Aussagekräftige Namen** - `test_home_game_parsing()` statt `test_1()`
4. **Fixtures nutzen** - Für wiederverwendbare Test-Daten
5. **Parametrisierung** - Teste mehrere Inputs mit einem Test
6. **Mocking** - Für externe Abhängigkeiten (Dateien, Netzwerk)

## 🐛 Debugging

### In VS Code:
1. Setze einen Breakpoint (klicke links neben die Zeilennummer)
2. Klicke auf das 🪲 Debug-Symbol neben dem Test
3. Nutze die Debug-Tools (Step Over, Step Into, etc.)

### In der Kommandozeile:
```bash
# Mit pdb debuggen
pytest --pdb  # Stoppt bei jedem Fehler

# Mit ipdb (besseres Interface)
pip install ipdb
pytest --pdb --pdbcls=IPython.terminal.debugger:TerminalPdb
```

## 📚 Weitere Ressourcen

- [Pytest Dokumentation](https://docs.pytest.org/)
- [VS Code Python Testing](https://code.visualstudio.com/docs/python/testing)
- [Real Python: Testing Guide](https://realpython.com/pytest-python-testing/)

## ⚡ Schnellstart-Checkliste

- [ ] Virtuelle Umgebung erstellt und aktiviert
- [ ] `pip install -r requirements-test.txt` ausgeführt
- [ ] VS Code Extensions installiert
- [ ] `.vscode/` Ordner mit Config-Dateien erstellt
- [ ] Tests ausgeführt: `pytest -v`
- [ ] Tests im VS Code Testing Panel sichtbar
- [ ] Coverage-Report generiert: `pytest --cov=.`

## 💡 Nächste Schritte

1. Erweitere die Tests um fehlende Funktionen
2. Füge Integration Tests hinzu
3. Erhöhe Code Coverage auf >80%
4. Richte Pre-Commit Hooks ein
5. Integriere CI/CD Pipeline

---

**Fragen oder Probleme?** Öffne ein Issue oder kontaktiere das Team!
