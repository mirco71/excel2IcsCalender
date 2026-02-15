import pandas as pd
import csv
from pathlib import Path
from datetime import datetime, timedelta
from ics import Calendar, Event  #pip install ics
import re
from zoneinfo import ZoneInfo

# === Konfiguration ===
excel_file = "2025-2026_Trainingsplan Master.xlsx"
sheet_name = "2026 Master"
output_dir_csv = Path("calendar_csv")
output_dir_ics = Path("calendar_ics")
output_dir_csv.mkdir(exist_ok=True)
output_dir_ics.mkdir(exist_ok=True)
berlin_tz = ZoneInfo("Europe/Berlin")

# Google-CSV-Format Spalten
csv_columns = [
    "Subject", "Start Date", "Start Time", "End Date", "End Time",
    "All Day Event", "Description", "Location", "Private"
]

# --- Hilfsfunktionen ---
def clean_time_str(time_val) -> str:
    if pd.isna(time_val):
        return None
    if hasattr(time_val, "strftime"):
        return time_val.strftime("%H:%M")
    if not isinstance(time_val, str):
        time_val = str(time_val)
    time_val = time_val.strip()
    if re.match(r"^\d{1,2}:\d{2}$", time_val):
        return time_val
    digits = re.findall(r"\d+", time_val)
    if len(digits) == 2:
        return f"{int(digits[0]):02d}:{int(digits[1]):02d}"
    elif len(digits) == 1 and len(digits[0]) == 4:
        return f"{digits[0][:2]}:{digits[0][2:]}"
    else:
        raise ValueError(f"Ungültige Uhrzeit: {time_val}")

def is_training_time(cell_value) -> bool:
    if isinstance(cell_value, datetime) or hasattr(cell_value, "strftime"):
        return False
    if not isinstance(cell_value, str):
        return False
    return "-" in cell_value and all(part.strip().replace(":", "").isdigit()
                                     for part in cell_value.split("-"))

def parse_time_range(time_str: str):
    parts = time_str.split("-")
    start = parts[0].strip()
    end = parts[1].strip()
    return start, end

def parse_game(cell_value):
    if not isinstance(cell_value, str):
        cell_value = str(cell_value)
    parts = cell_value.split(" ", 2)
    if len(parts) < 3:
        return None
    game_type = parts[0].strip()
    start_time = parts[1].strip()
    opponent = parts[2].strip()
    if game_type.upper() == "A":
        location = opponent
        title = f"Auswärtsspiel in {opponent}"
    elif game_type.upper() == "H":
        location = "Solingen"
        title = f"Heimspiel gegen {opponent}"
    else:
        return None
    return title, start_time, location

# === Excel laden ===
df = pd.read_excel(excel_file, sheet_name=sheet_name)
date_col = df.columns[0]
team_cols = df.columns[5:16]  # F–P

# Gemeinsame Kalender/CSV für U11A und U11B
u11_rows = []
u11_calendar = Calendar()

for team in team_cols:
    # Wenn Team U11A oder U11B → gemeinsame Verarbeitung
    if team in ["U11A", "U11B"]:
        target_rows = u11_rows
        target_calendar = u11_calendar
    else:
        target_rows = []
        target_calendar = Calendar()

    for _, row in df.iterrows():
        date_val = row[date_col]
        if isinstance(date_val, str) and date_val.strip().lower() == "datum":
            continue
        if pd.isna(date_val):
            continue

        cell_val = row[team]
        if pd.isna(cell_val):
            continue

        # Training
        if team != "U11B":
            if isinstance(cell_val, str) and is_training_time(cell_val):
                start_time, end_time = parse_time_range(cell_val)
                start_time = clean_time_str(start_time)
                end_time = clean_time_str(end_time)

                if team == "U11A":
                    subject = "U11 Training"
                else:
                    subject = team + " Training"
                target_rows.append({
                    "Subject": subject,
                    "Start Date": date_val.strftime("%m/%d/%Y"),
                    "Start Time": start_time,
                    "End Date": date_val.strftime("%m/%d/%Y"),
                    "End Time": end_time,
                    "All Day Event": "False",
                    "Description": "",
                    "Location": "",
                    "Private": "False"
                })

                start_dt = datetime.strptime(f"{date_val.strftime('%Y-%m-%d')} {start_time}", "%Y-%m-%d %H:%M")#.replace(tzinfo=berlin_tz)
                end_dt = datetime.strptime(f"{date_val.strftime('%Y-%m-%d')} {end_time}", "%Y-%m-%d %H:%M")#.replace(tzinfo=berlin_tz)
                event = Event()
                event.name = subject
                event.begin = start_dt
                event.end = end_dt
                target_calendar.events.add(event)
                continue

        # Spiel
        game_info = parse_game(cell_val)
        if game_info:
            title, start_time, location = game_info
            start_time = clean_time_str(start_time)
            start_dt = datetime.strptime(f"{date_val.strftime('%Y-%m-%d')} {start_time}", "%Y-%m-%d %H:%M")#.replace(tzinfo=berlin_tz)
            end_dt = start_dt + timedelta(hours=3)

            target_rows.append({
                "Subject": team + " " + title,
                "Start Date": date_val.strftime("%m/%d/%Y"),
                "Start Time": start_time,
                "End Date": date_val.strftime("%m/%d/%Y"),
                "End Time": end_dt.strftime("%H:%M"),
                "All Day Event": "False",
                "Description": "",
                "Location": location,
                "Private": "False"
            })

            event = Event()
            event.name = team + " " + title
            event.begin = start_dt
            event.end = end_dt
            event.location = location
            target_calendar.events.add(event)
            continue

    # Speichern für alle außer U11A/U11B direkt hier
    if team not in ["U11A", "U11B"]:
        csv_file = output_dir_csv / f"{team.replace(' ', '_')}.csv"
        with open(csv_file, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=csv_columns)
            writer.writeheader()
            writer.writerows(target_rows)

        ics_file = output_dir_ics / f"{team.replace(' ', '_')}.ics"
        with open(ics_file, mode="w", encoding="utf-8") as f:
            f.writelines(target_calendar)

# Am Ende: Gemeinsame U11-Dateien speichern
csv_file = output_dir_csv / "U11.csv"
with open(csv_file, mode="w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=csv_columns)
    writer.writeheader()
    writer.writerows(u11_rows)

ics_file = output_dir_ics / "U11.ics"
with open(ics_file, mode="w", encoding="utf-8") as f:
    f.writelines(u11_calendar)

print(f"CSV-Dateien erstellt im Ordner: {output_dir_csv.resolve()}")
print(f"ICS-Dateien erstellt im Ordner: {output_dir_ics.resolve()}")