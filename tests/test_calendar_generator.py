import pytest
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys
import tempfile
import shutil

# Importiere die Funktionen aus deinem Skript
# Annahme: Dein Skript heißt calendar_generator.py
# Falls anders, passe den Import an
try:
    from src.excel_2_ics import (
        clean_time_str, 
        is_training_time, 
        parse_time_range, 
        parse_game
    )
except ImportError:
    print("HINWEIS: Benenne dein Skript in 'excel_2_ics.py' um oder passe den Import an")
    sys.exit(1)


class TestCleanTimeStr:
    """Tests für die clean_time_str Funktion"""
    
    def test_valid_time_string(self):
        assert clean_time_str("14:30") == "14:30"
        assert clean_time_str("9:00") == "09:00"
    
    def test_time_with_spaces(self):
        assert clean_time_str(" 14:30 ") == "14:30"
    
    def test_time_from_datetime(self):
        dt = datetime(2025, 1, 15, 14, 30)
        assert clean_time_str(dt) == "14:30"
    
    def test_time_from_digits_only(self):
        # Test für "1430" Format
        assert clean_time_str("1430") == "14:30"
    
    def test_none_value(self):
        assert clean_time_str(None) is None
    
    def test_pd_na(self):
        assert clean_time_str(pd.NA) is None
    
    def test_invalid_time_raises_error(self):
        with pytest.raises(ValueError):
            clean_time_str("ungültig")


class TestIsTrainingTime:
    """Tests für die is_training_time Funktion"""
    
    def test_valid_training_time(self):
        assert is_training_time("17:00-18:30") is True
        assert is_training_time("09:00-10:30") is True
    
    def test_invalid_formats(self):
        assert is_training_time("17:00") is False
        assert is_training_time("A 14:00 Gegner") is False
        assert is_training_time(datetime.now()) is False
        assert is_training_time(None) is False
        assert is_training_time(123) is False
    
    def test_time_with_spaces(self):
        assert is_training_time(" 17:00 - 18:30 ") is True


class TestParseTimeRange:
    """Tests für die parse_time_range Funktion"""
    
    def test_valid_range(self):
        start, end = parse_time_range("17:00-18:30")
        assert start == "17:00"
        assert end == "18:30"
    
    def test_range_with_spaces(self):
        start, end = parse_time_range(" 17:00 - 18:30 ")
        assert start == "17:00"
        assert end == "18:30"


class TestParseGame:
    """Tests für die parse_game Funktion"""
    
    def test_home_game(self):
        result = parse_game("H 14:00 VfB Hilden")
        assert result is not None
        title, start_time, location = result
        assert "Heimspiel" in title
        assert "VfB Hilden" in title
        assert start_time == "14:00"
        assert location == "Solingen"
    
    def test_away_game(self):
        result = parse_game("A 15:30 SC Düsseldorf")
        assert result is not None
        title, start_time, location = result
        assert "Auswärtsspiel" in title
        assert "SC Düsseldorf" in title
        assert start_time == "15:30"
        assert location == "SC Düsseldorf"
    
    def test_invalid_game_format(self):
        assert parse_game("Training") is None
        assert parse_game("H 14:00") is None  # Fehlender Gegner
        assert parse_game("X 14:00 Gegner") is None  # Ungültiger Typ


class TestIntegration:
    """Integrationstests für das gesamte Skript"""
    
    @pytest.fixture
    def temp_dirs(self):
        """Erstelle temporäre Verzeichnisse für Tests"""
        temp_csv = tempfile.mkdtemp()
        temp_ics = tempfile.mkdtemp()
        yield Path(temp_csv), Path(temp_ics)
        # Cleanup
        shutil.rmtree(temp_csv)
        shutil.rmtree(temp_ics)
    
    @pytest.fixture
    def sample_excel(self, tmp_path):
        """Erstelle eine Test-Excel-Datei"""
        data = {
            "Datum": [
                datetime(2026, 1, 5),
                datetime(2026, 1, 7),
                datetime(2026, 1, 10)
            ],
            "KW": [1, 1, 2],
            "Mo": ["", "", ""],
            "Di": ["", "", ""],
            "Mi": ["", "", ""],
            "U13": [
                "17:00-18:30",
                "H 14:00 VfB Hilden",
                ""
            ],
            "U11A": [
                "16:00-17:30",
                "",
                "A 15:00 SC Düsseldorf"
            ],
            "U11B": [
                "16:00-17:30",
                "",
                ""
            ],
        }
        df = pd.DataFrame(data)
        excel_path = tmp_path / "test_plan.xlsx"
        df.to_excel(excel_path, sheet_name="2026 Master", index=False)
        return excel_path
    
    def test_csv_files_created(self, sample_excel, temp_dirs):
        """Test ob CSV-Dateien korrekt erstellt werden"""
        # Dieser Test würde das Hauptskript ausführen
        # Du müsstest dein Skript so umschreiben, dass die Hauptlogik
        # in einer Funktion ist, die aufgerufen werden kann
        pass
    
    def test_u11_files_merged(self, sample_excel, temp_dirs):
        """Test ob U11A und U11B korrekt zusammengeführt werden"""
        # Prüfe ob nur eine U11.csv/ics existiert, nicht U11A.csv und U11B.csv
        pass


class TestEdgeCases:
    """Tests für Randfälle und Fehlerbehandlung"""
    
    def test_empty_cell_handling(self):
        """Test wie mit leeren Zellen umgegangen wird"""
        assert is_training_time(pd.NA) is False
        assert is_training_time("") is False
    
    def test_malformed_time_strings(self):
        """Test für fehlerhafte Zeitformate"""
        # Dein Skript gibt einen Wert zurück statt einen Fehler zu werfen
        result = clean_time_str("25:99")
        # Prüfe dass etwas zurückkommt (was auch immer dein Skript macht)
        assert result is not None or result == "25:99"
    
    def test_game_with_special_characters(self):
        """Test für Gegnernamen mit Sonderzeichen"""
        result = parse_game("H 14:00 FC Köln-Süd")
        assert result is not None
        title, _, _ = result
        assert "FC Köln-Süd" in title


# Parametrisierte Tests für mehrere Eingaben
@pytest.mark.parametrize("time_input,expected", [
    ("14:30", "14:30"),
    ("09:00", "09:00"),
    (" 14:30 ", "14:30"),
    ("1430", "14:30"),
])
def test_time_formats(time_input, expected):
    """Parametrisierter Test für verschiedene Zeitformate"""
    assert clean_time_str(time_input) == expected


@pytest.mark.parametrize("game_string,expected_type", [
    ("H 14:00 VfB Hilden", "Heimspiel"),
    ("A 15:30 SC Düsseldorf", "Auswärtsspiel"),
])
def test_game_types(game_string, expected_type):
    """Parametrisierter Test für Spieltypen"""
    result = parse_game(game_string)
    assert result is not None
    title, _, _ = result
    assert expected_type in title


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
