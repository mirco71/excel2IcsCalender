# ⚽ Trainingsplan Kalender Generator

Automatische Konvertierung von Excel-Trainingsplänen in Kalenderformate (CSV & ICS) für Jugendmannschaften.

> **Hinweis zum Stand:** Dieses Repository enthält inzwischen **zwei** Wege.
> Der neue ist die [Kalender-Bridge](#-ecb-kalender-bridge) (Kalenderview →
> Google), der alte die Excel-Umwandlung darunter. Sobald die Bridge produktiv
> läuft, wird der Excel-Weg nicht mehr gebraucht — die Termine kommen dann aus
> Hallenplanung über Kalenderview.

## 🌉 ECB Kalender-Bridge

Holt für jedes Team den öffentlichen iCalendar-Feed aus
[Kalenderview](https://github.com/mirco71/ECB_Kalenderview) und gleicht ihn
gegen den zugehörigen Google-Kalender ab.

**Was sich gegenüber dem alten `clear_n_update.py` ändert:**

| | alt | neu |
|---|---|---|
| Vorgehen | alle Termine löschen, neu anlegen | gezielt anlegen, ändern, löschen |
| Abonnenten | sehen bei jedem Lauf alles als „neu" | sehen nur echte Änderungen |
| Abbruch mittendrin | halb leerer Kalender | unvollständiger Lauf, nächster repariert ihn |
| Fremde Termine im Kalender | wurden mitgelöscht | bleiben unangetastet |
| Anmeldung | OAuth mit Browserfenster | Dienstkonto, ohne Bildschirm nutzbar |

Möglich wird das durch zwei Dinge: die **stabile `iCalUID`** aus Hallenplanung,
über die Google einen verschobenen Termin als denselben erkennt, und die
Markierung `extendedProperties.private.ecb_bridge` an jedem selbst angelegten
Termin — aufgeräumt wird ausschließlich in dieser Menge.

### Aufruf

```bash
python -m src.bridge                    # alle konfigurierten Kalender, einmal
python -m src.bridge --dry-run          # nur anzeigen, nichts schreiben
python -m src.bridge --team U17         # nur ein Team
python -m src.bridge --interval 900     # Dauerbetrieb, alle 15 Minuten
```

### Konfiguration

| Variable | Bedeutung |
|---|---|
| `ECB_CALENDARS` | JSON-Objekt Team → Kalender-ID, z.B. `{"U17": "abc@group.calendar.google.com"}` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Pfad auf die Dienstkonto-Schlüsseldatei |
| `ECB_FEED_BASE` | Basis-URL der Feeds, Vorgabe `http://ecb-kalender:3000/feeds` |
| `ECB_PAST_DAYS` | Wie weit zurück verwaltet wird, Vorgabe 30 Tage |

Die Einrichtung des Dienstkontos (Google Cloud Console, Freigabe der zehn
Kalender) ist im Projektplan unter „Google-Dienstkonto einrichten" beschrieben.

### Betrieb

Als Dienst im selben Portainer-Stack wie Kalenderview, siehe
[`docker-compose.bridge.yml`](docker-compose.bridge.yml). Dann erreicht die
Bridge Kalenderview über den Servicenamen im internen Docker-Netz, ohne Umweg
über das Internet.

**Erster Lauf immer gegen einen Wegwerf-Kalender**, nicht gegen die zehn
produktiven — und danach ein zweites Mal: Der muss `0 übertragen, 0 gelöscht`
melden. Das ist der Beweis, dass der Abgleich wiederholbar ist.

---

## 🎯 Features (Excel-Weg)

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
