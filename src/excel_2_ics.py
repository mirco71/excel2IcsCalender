"""
Verbessertes calendar_generator.py mit besserer Testbarkeit

WICHTIGE ÄNDERUNGEN:
1. Hauptlogik in testbare Funktionen ausgelagert
2. Klare Trennung von Konfiguration und Logik
3. Dependency Injection für besseres Testen
4. Fehlerbehandlung hinzugefügt
"""

import pandas as pd
import csv
from pathlib import Path
from datetime import datetime, timedelta
from ics import Calendar, Event
import re
from zoneinfo import ZoneInfo
from typing import Tuple, Optional, List, Dict
import logging

# Logging konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Konstanten ===
BERLIN_TZ = ZoneInfo("Europe/Berlin")
GAME_DURATION_HOURS = 3

CSV_COLUMNS = [
    "Subject", "Start Date", "Start Time", "End Date", "End Time",
    "All Day Event", "Description", "Location", "Private"
]


# --- Hilfsfunktionen ---
def clean_time_str(time_val) -> Optional[str]:
    """
    Konvertiert verschiedene Zeitformate in standardisiertes HH:MM Format.
    
    Args:
        time_val: Zeit als String, datetime oder andere Typen
        
    Returns:
        String im Format "HH:MM" oder None wenn ungültig
        
    Raises:
        ValueError: Wenn das Zeitformat nicht erkannt werden kann
    """
    if pd.isna(time_val):
        return None
    
    if hasattr(time_val, "strftime"):
        return time_val.strftime("%H:%M")
    
    if not isinstance(time_val, str):
        time_val = str(time_val)
    
    time_val = time_val.strip()
    
    # Format HH:MM
    if re.match(r"^\d{1,2}:\d{2}$", time_val):
        parts = time_val.split(":")
        return f"{int(parts[0]):02d}:{int(parts[1]):02d}"
    
    # Nur Zahlen
    digits = re.findall(r"\d+", time_val)
    if len(digits) == 2:
        return f"{int(digits[0]):02d}:{int(digits[1]):02d}"
    elif len(digits) == 1 and len(digits[0]) == 4:
        return f"{digits[0][:2]}:{digits[0][2:]}"
    else:
        raise ValueError(f"Ungültige Uhrzeit: {time_val}")


def is_training_time(cell_value) -> bool:
    """
    Prüft ob ein Zellwert ein Trainingszeitformat ist (HH:MM-HH:MM).
    
    Args:
        cell_value: Zu prüfender Wert
        
    Returns:
        True wenn Format einem Training entspricht
    """
    if isinstance(cell_value, datetime) or hasattr(cell_value, "strftime"):
        return False
    
    if not isinstance(cell_value, str):
        return False
    
    return "-" in cell_value and all(
        part.strip().replace(":", "").isdigit()
        for part in cell_value.split("-")
    )


def parse_time_range(time_str: str) -> Tuple[str, str]:
    """
    Splittet einen Zeitbereich in Start- und Endzeit.
    
    Args:
        time_str: Zeitbereich im Format "HH:MM-HH:MM"
        
    Returns:
        Tuple mit (start_time, end_time)
    """
    parts = time_str.split("-")
    start = parts[0].strip()
    end = parts[1].strip()
    return start, end


def parse_game(cell_value) -> Optional[Tuple[str, str, str]]:
    """
    Parst Spielinformationen aus einer Zelle.
    
    Args:
        cell_value: Zellwert im Format "A/H HH:MM Gegner"
        
    Returns:
        Tuple mit (title, start_time, location) oder None wenn ungültig
    """
    if not isinstance(cell_value, str):
        cell_value = str(cell_value)
    
    parts = cell_value.split(" ", 2)
    if len(parts) < 3:
        return None
    
    game_type = parts[0].strip().upper()
    start_time = parts[1].strip()
    opponent = parts[2].strip()
    
    if game_type == "A":
        location = opponent
        title = f"Auswärtsspiel in {opponent}"
    elif game_type == "H":
        location = "Solingen"
        title = f"Heimspiel gegen {opponent}"
    else:
        return None
    
    return title, start_time, location


class CalendarProcessor:
    """Klasse für die Verarbeitung des Trainingsplans."""
    
    def __init__(self, output_dir_csv: Path, output_dir_ics: Path):
        """
        Initialisiert den CalendarProcessor.
        
        Args:
            output_dir_csv: Ausgabeverzeichnis für CSV-Dateien
            output_dir_ics: Ausgabeverzeichnis für ICS-Dateien
        """
        self.output_dir_csv = output_dir_csv
        self.output_dir_ics = output_dir_ics
        self.output_dir_csv.mkdir(exist_ok=True)
        self.output_dir_ics.mkdir(exist_ok=True)
    
    def process_training_entry(
        self, 
        date_val: datetime, 
        time_str: str, 
        team: str
    ) -> Tuple[Dict, Event]:
        """
        Verarbeitet einen Trainingseintrag.
        
        Args:
            date_val: Datum des Trainings
            time_str: Zeitbereich des Trainings
            team: Team-Name
            
        Returns:
            Tuple mit (csv_row_dict, ics_event)
        """
        start_time, end_time = parse_time_range(time_str)
        start_time = clean_time_str(start_time)
        end_time = clean_time_str(end_time)
        
        subject = "U11 Training" if team == "U11A" else f"{team} Training"
        
        csv_row = {
            "Subject": subject,
            "Start Date": date_val.strftime("%m/%d/%Y"),
            "Start Time": start_time,
            "End Date": date_val.strftime("%m/%d/%Y"),
            "End Time": end_time,
            "All Day Event": "False",
            "Description": "",
            "Location": "",
            "Private": "False"
        }
        
        start_dt = datetime.strptime(
            f"{date_val.strftime('%Y-%m-%d')} {start_time}", 
            "%Y-%m-%d %H:%M"
        ).replace(tzinfo=BERLIN_TZ)
        end_dt = datetime.strptime(
            f"{date_val.strftime('%Y-%m-%d')} {end_time}", 
            "%Y-%m-%d %H:%M"
        ).replace(tzinfo=BERLIN_TZ)
        
        event = Event()
        event.name = subject
        event.begin = start_dt
        event.end = end_dt
        
        return csv_row, event
    
    def process_game_entry(
        self, 
        date_val: datetime, 
        cell_val: str, 
        team: str
    ) -> Tuple[Dict, Event]:
        """
        Verarbeitet einen Spieleintrag.
        
        Args:
            date_val: Datum des Spiels
            cell_val: Zellwert mit Spielinformationen
            team: Team-Name
            
        Returns:
            Tuple mit (csv_row_dict, ics_event)
        """
        game_info = parse_game(cell_val)
        if not game_info:
            raise ValueError(f"Ungültiges Spielformat: {cell_val}")
        
        title, start_time, location = game_info
        start_time = clean_time_str(start_time)
        
        start_dt = datetime.strptime(
            f"{date_val.strftime('%Y-%m-%d')} {start_time}", 
            "%Y-%m-%d %H:%M"
        ).replace(tzinfo=BERLIN_TZ)
        end_dt = start_dt + timedelta(hours=GAME_DURATION_HOURS)
        
        csv_row = {
            "Subject": f"{team} {title}",
            "Start Date": date_val.strftime("%m/%d/%Y"),
            "Start Time": start_time,
            "End Date": date_val.strftime("%m/%d/%Y"),
            "End Time": end_dt.strftime("%H:%M"),
            "All Day Event": "False",
            "Description": "",
            "Location": location,
            "Private": "False"
        }
        
        event = Event()
        event.name = f"{team} {title}"
        event.begin = start_dt
        event.end = end_dt
        event.location = location
        
        return csv_row, event
    
    def save_calendar(
        self, 
        team_name: str, 
        rows: List[Dict], 
        calendar: Calendar
    ) -> None:
        """
        Speichert Kalender als CSV und ICS.
        
        Args:
            team_name: Name des Teams
            rows: Liste von CSV-Zeilen
            calendar: ICS-Calendar Objekt
        """
        safe_name = team_name.replace(' ', '_')
        
        # CSV speichern
        csv_file = self.output_dir_csv / f"{safe_name}.csv"
        with open(csv_file, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
        logger.info(f"CSV erstellt: {csv_file}")
        
        # ICS speichern
        ics_file = self.output_dir_ics / f"{safe_name}.ics"
        with open(ics_file, mode="w", encoding="utf-8") as f:
            f.writelines(calendar)
        logger.info(f"ICS erstellt: {ics_file}")


def process_calendar(
    excel_file: str,
    sheet_name: str,
    output_dir_csv: Path,
    output_dir_ics: Path,
    date_column_index: int = 0,
    team_column_range: Tuple[int, int] = (5, 16)
) -> None:
    """
    Hauptfunktion zur Verarbeitung des Trainingsplans.
    
    Args:
        excel_file: Pfad zur Excel-Datei
        sheet_name: Name des Sheets
        output_dir_csv: Ausgabeverzeichnis für CSV
        output_dir_ics: Ausgabeverzeichnis für ICS
        date_column_index: Index der Datumsspalte
        team_column_range: Tuple mit (start, end) Index für Team-Spalten
    """
    logger.info(f"Verarbeite {excel_file}, Sheet: {sheet_name}")
    
    # Excel laden
    df = pd.read_excel(excel_file, sheet_name=sheet_name)
    date_col = df.columns[date_column_index]
    team_cols = df.columns[team_column_range[0]:team_column_range[1]]
    
    processor = CalendarProcessor(output_dir_csv, output_dir_ics)
    
    # U11 gemeinsam verarbeiten
    u11_rows = []
    u11_calendar = Calendar()
    
    for team in team_cols:
        # U11A und U11B zusammenführen
        if team in ["U11A", "U11B"]:
            target_rows = u11_rows
            target_calendar = u11_calendar
        else:
            target_rows = []
            target_calendar = Calendar()
        
        for _, row in df.iterrows():
            date_val = row[date_col]
            
            # Header überspringen
            if isinstance(date_val, str) and date_val.strip().lower() == "datum":
                continue
            
            if pd.isna(date_val):
                continue
            
            cell_val = row[team]
            if pd.isna(cell_val):
                continue
            
            try:
                # Training
                if team != "U11B" and is_training_time(cell_val):
                    csv_row, event = processor.process_training_entry(
                        date_val, cell_val, team
                    )
                    target_rows.append(csv_row)
                    target_calendar.events.add(event)
                    continue
                
                # Spiel
                if parse_game(cell_val):
                    csv_row, event = processor.process_game_entry(
                        date_val, cell_val, team
                    )
                    target_rows.append(csv_row)
                    target_calendar.events.add(event)
                    continue
                    
            except Exception as e:
                logger.error(
                    f"Fehler bei {team}, Datum {date_val}, Wert: {cell_val}: {e}"
                )
                continue
        
        # Speichern für einzelne Teams
        if team not in ["U11A", "U11B"]:
            processor.save_calendar(team, target_rows, target_calendar)
    
    # U11 gemeinsam speichern
    processor.save_calendar("U11", u11_rows, u11_calendar)
    
    logger.info("Verarbeitung abgeschlossen!")


def main():
    """Haupteinstiegspunkt des Skripts."""
    # Konfiguration
    excel_file = "2025-2026_Trainingsplan Master.xlsx"
    sheet_name = "2026 Master"
    output_dir_csv = Path("calendar_csv")
    output_dir_ics = Path("calendar_ics")
    
    try:
        process_calendar(
            excel_file=excel_file,
            sheet_name=sheet_name,
            output_dir_csv=output_dir_csv,
            output_dir_ics=output_dir_ics
        )
    except FileNotFoundError:
        logger.error(f"Excel-Datei nicht gefunden: {excel_file}")
    except Exception as e:
        logger.error(f"Fehler bei der Verarbeitung: {e}")
        raise


if __name__ == "__main__":
    main()
