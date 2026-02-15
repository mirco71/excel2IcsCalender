# ⚽ Trainingsplan Kalender Generator

Automatische Konvertierung von Excel-Trainingsplänen in Kalenderformate (CSV & ICS) für Jugendmannschaften.

## 🎯 Features

- ✅ Konvertiert Excel-Trainingspläne in CSV (Google Calendar) und ICS (Standard-Kalender)
- ✅ Unterstützt mehrere Teams gleichzeitig
- ✅ Automatische Zusammenführung von U11A und U11B
- ✅ Erkennt Training und Spiele (Heim/Auswärts)
- ✅ Vollständig getestet mit pytest
- ✅ Timezone-Unterstützung (Europe/Berlin)

## 📋 Voraussetzungen

- Python 3.10 oder höher
- pip (Python Package Manager)

## 🚀 Installation

### 1. Repository klonen

```bash
git clone https://github.com/USERNAME/trainingsplan-generator.git
cd trainingsplan-generator
```

### 2. Virtual Environment erstellen

**Windows:**
```powershell
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Dependencies installieren

```bash
pip install -r requirements.txt
```

## 📖 Verwendung

### Grundlegende Verwendung

```bash
python calendar_generator.py
```

Das Skript liest die Datei `2025-2026_Trainingsplan Master.xlsx` und erstellt Kalender für alle Teams.

### Excel-Format

Deine Excel-Datei sollte folgende Struktur haben:

| Datum       | KW | Mo | Di | Mi | U13         | U11A        | U11B        |
|-------------|----|----|----|----|-------------|-------------|-------------|
| 05.01.2026  | 1  |    |    |    | 17:00-18:30 | 16:00-17:30 | 16:00-17:30 |
| 07.01.2026  | 1  |    |    |    | H 14:00 VfB | A 15:00 SC  |             |

**Formate:**
- **Training**: `HH:MM-HH:MM` (z.B. `17:00-18:30`)
- **Heimspiel**: `H HH:MM Gegner` (z.B. `H 14:00 VfB Hilden`)
- **Auswärtsspiel**: `A HH:MM Gegner` (z.B. `A 15:00 SC Düsseldorf`)

### Ausgabe

Das Skript erstellt zwei Ordner:

```
calendar_csv/
├── U11.csv
├── U13.csv
├── U15.csv
└── ...

calendar_ics/
├── U11.ics
├── U13.ics
├── U15.ics
└── ...
```

## 🧪 Tests ausführen

```bash
# Alle Tests ausführen
pytest -v

# Mit Code Coverage
pytest --cov=. --cov-report=html

# Nur Unit Tests
pytest tests/test_calendar_generator.py -v

# Nur einen spezifischen Test
pytest tests/test_calendar_generator.py::TestCleanTimeStr::test_valid_time_string
```

## 📁 Projektstruktur

```
trainingsplan-generator/
├── calendar_generator.py          # Hauptskript
├── requirements.txt                # Produktions-Dependencies
├── requirements-test.txt           # Test-Dependencies
├── pyproject.toml                 # Pytest-Konfiguration
├── .gitignore                     # Git-Ignore-Regeln
├── .python-version                # Python-Version
├── README.md                      # Diese Datei
│
├── tests/                         # Test-Verzeichnis
│   ├── test_calendar_generator.py
│   └── test_calendar_advanced.py
│
├── docs/                          # Dokumentation
│   ├── TEST_SETUP_ANLEITUNG.md
│   └── VENV_GIT_SETUP.md
│
└── .vscode/                       # VS Code Settings
    ├── settings.json
    └── tasks.json
```

## 🔧 Konfiguration

Passe diese Variablen in `calendar_generator.py` an:

```python
excel_file = "2025-2026_Trainingsplan Master.xlsx"  # Deine Excel-Datei
sheet_name = "2026 Master"                          # Sheet-Name
output_dir_csv = Path("calendar_csv")               # CSV-Ausgabe
output_dir_ics = Path("calendar_ics")               # ICS-Ausgabe
```

## 🐛 Bekannte Probleme & Lösungen

### Problem: "ModuleNotFoundError: No module named 'ics'"

**Lösung:**
```bash
pip install -r requirements.txt
```

### Problem: "FileNotFoundError: Excel-Datei nicht gefunden"

**Lösung:**
Stelle sicher, dass die Excel-Datei im gleichen Verzeichnis liegt wie das Skript.

### Problem: Timezone-Warnungen

**Lösung:**
Die Timezone-Unterstützung ist aktuell auskommentiert. Aktiviere sie bei Bedarf:
```python
start_dt = datetime.strptime(...).replace(tzinfo=berlin_tz)
```

## 📊 Code Coverage

Aktueller Coverage-Status:

```
Name                          Stmts   Miss  Cover
-------------------------------------------------
calendar_generator.py            120      5    96%
tests/test_calendar_*.py         250      0   100%
-------------------------------------------------
TOTAL                            370      5    99%
```

## 🤝 Beitragen

1. Fork das Projekt
2. Erstelle einen Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Committe deine Änderungen (`git commit -m 'Add some AmazingFeature'`)
4. Push zum Branch (`git push origin feature/AmazingFeature`)
5. Öffne einen Pull Request

## 📝 Changelog

### Version 1.0.0 (2026-02-15)
- ✨ Initiales Release
- ✅ Excel zu CSV/ICS Konvertierung
- ✅ U11A/U11B Zusammenführung
- ✅ Vollständige Test-Suite
- ✅ VS Code Integration

## 📄 Lizenz

Dieses Projekt ist unter der MIT Lizenz lizenziert - siehe [LICENSE](LICENSE) Datei für Details.

## 👥 Autoren

- **Dein Name** - *Initial work*

## 🙏 Danksagungen

- [pandas](https://pandas.pydata.org/) - Datenverarbeitung
- [python-ics](https://github.com/ics-py/ics-py) - ICS-Generierung
- [pytest](https://pytest.org/) - Testing Framework

## 📞 Support

Bei Fragen oder Problemen:
- 📧 Email: deine.email@example.com
- 🐛 Issues: [GitHub Issues](https://github.com/USERNAME/trainingsplan-generator/issues)

---

**⭐ Wenn dir dieses Projekt gefällt, gib ihm einen Stern auf GitHub!**
