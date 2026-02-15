"""
Erweiterte Tests mit Mocking und Fixtures
"""

import pytest
import pandas as pd
from datetime import datetime
from pathlib import Path
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock

# Import der refactored Version
try:
    from src.excel_2_ics import (
        clean_time_str,
        is_training_time,
        parse_time_range,
        parse_game,
        CalendarProcessor,
        process_calendar,
        BERLIN_TZ
    )
except ImportError:
    print("Verwende calendar_generator_refactored.py")


# === Fixtures ===

@pytest.fixture
def temp_dirs():
    """Erstellt temporäre Verzeichnisse für Tests."""
    temp_csv = Path(tempfile.mkdtemp())
    temp_ics = Path(tempfile.mkdtemp())
    
    yield temp_csv, temp_ics
    
    # Cleanup
    shutil.rmtree(temp_csv, ignore_errors=True)
    shutil.rmtree(temp_ics, ignore_errors=True)


@pytest.fixture
def sample_dataframe():
    """Erstellt ein Test-DataFrame."""
    data = {
        "Datum": [
            datetime(2026, 1, 5),
            datetime(2026, 1, 7),
            datetime(2026, 1, 10),
            datetime(2026, 1, 12)
        ],
        "KW": [1, 1, 2, 2],
        "Mo": ["", "", "", ""],
        "Di": ["", "", "", ""],
        "Mi": ["", "", "", ""],
        "U13": [
            "17:00-18:30",
            "H 14:00 VfB Hilden",
            "",
            "A 15:30 SC Düsseldorf"
        ],
        "U11A": [
            "16:00-17:30",
            "",
            "A 15:00 SC Düsseldorf",
            ""
        ],
        "U11B": [
            "16:00-17:30",
            "",
            "",
            ""
        ],
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_excel_file(tmp_path, sample_dataframe):
    """Erstellt eine temporäre Excel-Datei."""
    excel_path = tmp_path / "test_trainingsplan.xlsx"
    sample_dataframe.to_excel(excel_path, sheet_name="2026 Master", index=False)
    return excel_path


@pytest.fixture
def calendar_processor(temp_dirs):
    """Erstellt einen CalendarProcessor mit temporären Verzeichnissen."""
    csv_dir, ics_dir = temp_dirs
    return CalendarProcessor(csv_dir, ics_dir)


# === Unit Tests ===

class TestCleanTimeStr:
    """Umfassende Tests für clean_time_str."""
    
    @pytest.mark.parametrize("input_val,expected", [
        ("14:30", "14:30"),
        ("9:00", "09:00"),
        (" 14:30 ", "14:30"),
        ("1430", "14:30"),
        ("09:05", "09:05"),
    ])
    def test_various_valid_formats(self, input_val, expected):
        """Test verschiedene gültige Zeitformate."""
        assert clean_time_str(input_val) == expected
    
    def test_datetime_object(self):
        """Test mit datetime Objekt."""
        dt = datetime(2025, 1, 15, 14, 30)
        assert clean_time_str(dt) == "14:30"
    
    def test_none_and_na_values(self):
        """Test mit None und NA Werten."""
        assert clean_time_str(None) is None
        assert clean_time_str(pd.NA) is None
    
    def test_invalid_format_raises_error(self):
        """Test dass ungültige Formate Fehler werfen."""
        with pytest.raises(ValueError, match="Ungültige Uhrzeit"):
            clean_time_str("not_a_time")


class TestIsTrainingTime:
    """Tests für is_training_time."""
    
    @pytest.mark.parametrize("input_val,expected", [
        ("17:00-18:30", True),
        ("9:00-10:30", True),
        (" 17:00 - 18:30 ", True),
        ("17:00", False),
        ("A 14:00 Gegner", False),
        (None, False),
        (123, False),
    ])
    def test_various_inputs(self, input_val, expected):
        """Test verschiedene Eingaben."""
        assert is_training_time(input_val) == expected
    
    def test_datetime_object(self):
        """Test dass datetime Objekte False zurückgeben."""
        assert is_training_time(datetime.now()) is False


class TestParseGame:
    """Tests für parse_game mit verschiedenen Szenarien."""
    
    def test_home_game_standard(self):
        """Test Standard-Heimspiel."""
        result = parse_game("H 14:00 VfB Hilden")
        assert result is not None
        title, time, location = result
        assert "Heimspiel" in title
        assert "VfB Hilden" in title
        assert time == "14:00"
        assert location == "Solingen"
    
    def test_away_game_standard(self):
        """Test Standard-Auswärtsspiel."""
        result = parse_game("A 15:30 SC Düsseldorf")
        assert result is not None
        title, time, location = result
        assert "Auswärtsspiel" in title
        assert "SC Düsseldorf" in title
        assert time == "15:30"
        assert location == "SC Düsseldorf"
    
    def test_case_insensitive(self):
        """Test dass H/A case-insensitive sind."""
        result_lower = parse_game("h 14:00 Test")
        result_upper = parse_game("H 14:00 Test")
        assert result_lower is not None
        assert result_upper is not None
    
    def test_opponent_with_special_chars(self):
        """Test Gegnernamen mit Sonderzeichen."""
        result = parse_game("H 14:00 FC Köln-Süd 1860")
        assert result is not None
        _, _, _ = result
    
    @pytest.mark.parametrize("invalid_input", [
        "Training",
        "H 14:00",  # Fehlender Gegner
        "X 14:00 Gegner",  # Ungültiger Typ
        "14:00 Gegner",  # Fehlender Typ
    ])
    def test_invalid_formats(self, invalid_input):
        """Test dass ungültige Formate None zurückgeben."""
        assert parse_game(invalid_input) is None


# === CalendarProcessor Tests ===

class TestCalendarProcessor:
    """Tests für die CalendarProcessor Klasse."""
    
    def test_initialization(self, temp_dirs):
        """Test dass Verzeichnisse erstellt werden."""
        csv_dir, ics_dir = temp_dirs
        processor = CalendarProcessor(csv_dir, ics_dir)
        
        assert processor.output_dir_csv.exists()
        assert processor.output_dir_ics.exists()
    
    def test_process_training_entry(self, calendar_processor):
        """Test Verarbeitung eines Trainingseintrags."""
        date_val = datetime(2026, 1, 5)
        time_str = "17:00-18:30"
        team = "U13"
        
        csv_row, event = calendar_processor.process_training_entry(
            date_val, time_str, team
        )
        
        assert csv_row["Subject"] == "U13 Training"
        assert csv_row["Start Time"] == "17:00"
        assert csv_row["End Time"] == "18:30"
        assert event.name == "U13 Training"
    
    def test_process_training_entry_u11a(self, calendar_processor):
        """Test dass U11A als 'U11 Training' gespeichert wird."""
        date_val = datetime(2026, 1, 5)
        time_str = "16:00-17:30"
        team = "U11A"
        
        csv_row, event = calendar_processor.process_training_entry(
            date_val, time_str, team
        )
        
        assert csv_row["Subject"] == "U11 Training"
        assert event.name == "U11 Training"
    
    def test_process_game_entry_home(self, calendar_processor):
        """Test Verarbeitung eines Heimspiels."""
        date_val = datetime(2026, 1, 7)
        cell_val = "H 14:00 VfB Hilden"
        team = "U13"
        
        csv_row, event = calendar_processor.process_game_entry(
            date_val, cell_val, team
        )
        
        assert "Heimspiel" in csv_row["Subject"]
        assert csv_row["Location"] == "Solingen"
        assert event.location == "Solingen"
    
    def test_process_game_entry_away(self, calendar_processor):
        """Test Verarbeitung eines Auswärtsspiels."""
        date_val = datetime(2026, 1, 10)
        cell_val = "A 15:00 SC Düsseldorf"
        team = "U13"
        
        csv_row, event = calendar_processor.process_game_entry(
            date_val, cell_val, team
        )
        
        assert "Auswärtsspiel" in csv_row["Subject"]
        assert csv_row["Location"] == "SC Düsseldorf"
        assert event.location == "SC Düsseldorf"
    
    def test_save_calendar(self, calendar_processor):
        """Test dass Kalender korrekt gespeichert werden."""
        from ics import Calendar
        
        team_name = "U13"
        rows = [
            {
                "Subject": "U13 Training",
                "Start Date": "01/05/2026",
                "Start Time": "17:00",
                "End Date": "01/05/2026",
                "End Time": "18:30",
                "All Day Event": "False",
                "Description": "",
                "Location": "",
                "Private": "False"
            }
        ]
        calendar = Calendar()
        
        calendar_processor.save_calendar(team_name, rows, calendar)
        
        csv_file = calendar_processor.output_dir_csv / "U13.csv"
        ics_file = calendar_processor.output_dir_ics / "U13.ics"
        
        assert csv_file.exists()
        assert ics_file.exists()


# === Integration Tests ===

class TestIntegration:
    """Integrationstests für das gesamte System."""
    
    def test_process_calendar_creates_files(
        self, 
        sample_excel_file, 
        temp_dirs
    ):
        """Test dass process_calendar alle Dateien erstellt."""
        csv_dir, ics_dir = temp_dirs
        
        process_calendar(
            excel_file=str(sample_excel_file),
            sheet_name="2026 Master",
            output_dir_csv=csv_dir,
            output_dir_ics=ics_dir
        )
        
        # Prüfe ob Dateien erstellt wurden
        csv_files = list(csv_dir.glob("*.csv"))
        ics_files = list(ics_dir.glob("*.ics"))
        
        assert len(csv_files) > 0, "Keine CSV-Dateien erstellt"
        assert len(ics_files) > 0, "Keine ICS-Dateien erstellt"
    
    def test_u11_files_merged(
        self, 
        sample_excel_file, 
        temp_dirs
    ):
        """Test dass U11A und U11B zusammengeführt werden."""
        csv_dir, ics_dir = temp_dirs
        
        process_calendar(
            excel_file=str(sample_excel_file),
            sheet_name="2026 Master",
            output_dir_csv=csv_dir,
            output_dir_ics=ics_dir
        )
        
        # Es sollte eine U11.csv geben, aber keine U11A.csv oder U11B.csv
        assert (csv_dir / "U11.csv").exists()
        assert (ics_dir / "U11.ics").exists()
        assert not (csv_dir / "U11A.csv").exists()
        assert not (csv_dir / "U11B.csv").exists()
    
    def test_u13_separate_file(
        self, 
        sample_excel_file, 
        temp_dirs
    ):
        """Test dass andere Teams separate Dateien bekommen."""
        csv_dir, ics_dir = temp_dirs
        
        process_calendar(
            excel_file=str(sample_excel_file),
            sheet_name="2026 Master",
            output_dir_csv=csv_dir,
            output_dir_ics=ics_dir
        )
        
        assert (csv_dir / "U13.csv").exists()
        assert (ics_dir / "U13.ics").exists()


# === Mocking Tests ===

class TestWithMocking:
    """Tests mit Mocking für externe Abhängigkeiten."""
    
    @patch('calendar_generator_refactored.pd.read_excel')
    def test_process_calendar_with_mock_excel(
        self, 
        mock_read_excel, 
        sample_dataframe,
        temp_dirs
    ):
        """Test mit gemocktem Excel-Lesen."""
        mock_read_excel.return_value = sample_dataframe
        csv_dir, ics_dir = temp_dirs
        
        process_calendar(
            excel_file="fake_file.xlsx",
            sheet_name="2026 Master",
            output_dir_csv=csv_dir,
            output_dir_ics=ics_dir
        )
        
        mock_read_excel.assert_called_once()
    
    def test_error_handling_invalid_excel(self, temp_dirs):
        """Test Fehlerbehandlung bei ungültiger Excel-Datei."""
        csv_dir, ics_dir = temp_dirs
        
        with pytest.raises(FileNotFoundError):
            process_calendar(
                excel_file="non_existent_file.xlsx",
                sheet_name="2026 Master",
                output_dir_csv=csv_dir,
                output_dir_ics=ics_dir
            )


# === Performance Tests ===

@pytest.mark.slow
class TestPerformance:
    """Performance-Tests (als langsam markiert)."""
    
    def test_large_dataset_performance(self, tmp_path):
        """Test Performance mit großem Datensatz."""
        # Erstelle großes DataFrame
        dates = pd.date_range('2026-01-01', periods=365)
        data = {
            "Datum": dates,
            "U13": ["17:00-18:30"] * 365
        }
        df = pd.DataFrame(data)
        
        excel_path = tmp_path / "large_test.xlsx"
        df.to_excel(excel_path, sheet_name="2026 Master", index=False)
        
        csv_dir = tmp_path / "csv"
        ics_dir = tmp_path / "ics"
        
        import time
        start = time.time()
        
        process_calendar(
            excel_file=str(excel_path),
            sheet_name="2026 Master",
            output_dir_csv=csv_dir,
            output_dir_ics=ics_dir,
            team_column_range=(1, 2)  # Nur eine Spalte
        )
        
        duration = time.time() - start
        
        assert duration < 10, f"Verarbeitung zu langsam: {duration}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=calendar_generator_refactored"])
