# 🚀 Schnellreferenz - Trainingsplan Generator

## 📦 Erste Schritte (Einmalig)

### Windows
```powershell
# 1. Setup-Skript ausführen
.\setup.bat

# 2. Git konfigurieren
git config --global user.name "Dein Name"
git config --global user.email "deine.email@example.com"

# 3. Repository erstellen
git init
git add .
git commit -m "Initial commit"
```

### macOS/Linux
```bash
# 1. Setup-Skript ausführbar machen
chmod +x setup.sh git-setup.sh

# 2. Setup ausführen
./setup.sh

# 3. Git Setup
./git-setup.sh
```

## 🔄 Tägliche Verwendung

### Environment aktivieren

**Windows:**
```powershell
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### Skript ausführen

```bash
python calendar_generator.py
```

### Tests ausführen

```bash
# Alle Tests
pytest -v

# Mit Coverage
pytest --cov=. --cov-report=html

# Einzelner Test
pytest tests/test_calendar_generator.py::TestCleanTimeStr -v
```

## 📝 Git Workflow

```bash
# Status prüfen
git status

# Änderungen hinzufügen
git add .

# Oder einzelne Datei
git add calendar_generator.py

# Commit erstellen
git commit -m "Beschreibung der Änderungen"

# Zu GitHub pushen
git push

# Von GitHub pullen
git pull
```

## 🔧 Häufige Aufgaben

### Neue Dependency hinzufügen

```bash
# Paket installieren
pip install neues-paket

# Requirements aktualisieren
pip freeze > requirements.txt

# In Git committen
git add requirements.txt
git commit -m "Add neues-paket dependency"
```

### Tests für neue Funktion schreiben

```python
# In test_calendar_generator.py
def test_meine_neue_funktion():
    result = meine_neue_funktion("input")
    assert result == "expected"
```

### Environment neu erstellen

```bash
# Altes Environment löschen
rm -rf venv  # macOS/Linux
rmdir /s venv  # Windows

# Neu erstellen
python -m venv venv

# Aktivieren
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Dependencies installieren
pip install -r requirements.txt
pip install -r requirements-test.txt
```

## 🐛 Debugging

### VS Code Debugger nutzen

1. Breakpoint setzen (Klick links neben Zeilennummer)
2. F5 drücken
3. Variablen inspizieren

### Print-Debugging

```python
print(f"Debug: variable = {variable}")
```

### pdb nutzen

```python
import pdb; pdb.set_trace()
```

## 📊 Code-Qualität

### Tests ausführen

```bash
pytest -v                           # Alle Tests
pytest -x                           # Stoppe bei erstem Fehler
pytest --lf                         # Nur letzte fehlgeschlagene Tests
pytest -k "test_clean"              # Nur Tests mit "clean" im Namen
pytest tests/test_calendar_generator.py  # Nur eine Datei
```

### Coverage prüfen

```bash
pytest --cov=. --cov-report=html
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows
```

### Code formatieren

```bash
pip install black
black calendar_generator.py
```

### Linting

```bash
pip install flake8
flake8 calendar_generator.py
```

## 🔍 Nützliche Befehle

### Python

```bash
python --version                    # Python-Version
pip list                           # Installierte Pakete
pip list --outdated                # Veraltete Pakete
pip show pandas                    # Paket-Details
which python                       # Python-Pfad (macOS/Linux)
where python                       # Python-Pfad (Windows)
```

### Git

```bash
git status                         # Status
git log --oneline                  # Commit-Historie
git diff                           # Änderungen anzeigen
git branch                         # Branches anzeigen
git branch feature-name            # Neuen Branch erstellen
git checkout feature-name          # Branch wechseln
git merge feature-name             # Branch mergen
```

### VS Code

| Shortcut | Aktion |
|----------|--------|
| `Ctrl+Shift+P` | Command Palette |
| `Ctrl+`` | Terminal öffnen |
| `F5` | Debugger starten |
| `Ctrl+Shift+F` | In allen Dateien suchen |
| `Ctrl+P` | Datei öffnen |
| `Ctrl+Shift+F5` | Tests ausführen |

## 🆘 Problemlösung

### "pip: command not found"
```bash
python -m pip install --upgrade pip
```

### "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### Environment aktiviert sich nicht (Windows)
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Git verfolgt venv/
```bash
git rm -r --cached venv/
echo "venv/" >> .gitignore
git commit -m "Remove venv from tracking"
```

### Tests schlagen fehl
```bash
# Environment neu aufsetzen
rm -rf venv
python -m venv venv
source venv/bin/activate  # oder venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-test.txt
pytest -v
```

## 📚 Weitere Ressourcen

- [Python Docs](https://docs.python.org/3/)
- [pytest Docs](https://docs.pytest.org/)
- [Git Docs](https://git-scm.com/doc)
- [VS Code Python](https://code.visualstudio.com/docs/python/python-tutorial)

## 💡 Tipps & Tricks

### Auto-Aktivierung des venv in VS Code

VS Code aktiviert automatisch das venv, wenn du:
1. Python Interpreter ausgewählt hast (`Ctrl+Shift+P` → "Python: Select Interpreter")
2. Ein neues Terminal öffnest

### Pre-Commit Hooks einrichten

```bash
pip install pre-commit
pre-commit install
```

Jetzt werden vor jedem Commit automatisch Tests ausgeführt!

### Aliases erstellen

**Bash (~/.bashrc oder ~/.zshrc):**
```bash
alias venv-activate='source venv/bin/activate'
alias run-tests='pytest -v'
alias run-coverage='pytest --cov=. --cov-report=html'
```

**PowerShell (Profile):**
```powershell
function Activate-Venv { venv\Scripts\activate }
Set-Alias venv Activate-Venv
```

## 🎯 Checkliste vor Git Push

- [ ] Tests laufen durch (`pytest -v`)
- [ ] Code formatiert (`black .`)
- [ ] Keine Secrets im Code
- [ ] requirements.txt aktualisiert
- [ ] Commit-Message ist aussagekräftig
- [ ] `.gitignore` ist aktuell

## 📞 Hilfe

Bei Problemen:
1. Lies die Fehlermeldung aufmerksam
2. Prüfe `git status` und `pip list`
3. Konsultiere die ausführlichen Anleitungen:
   - `VENV_GIT_SETUP.md`
   - `TEST_SETUP_ANLEITUNG.md`
4. Öffne ein Issue auf GitHub

---

**Zuletzt aktualisiert:** 2026-02-15
