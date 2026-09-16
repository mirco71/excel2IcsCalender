"""Tests für den Abgleich Kalenderview → Google.

Die Google-API steckt hinter einem schmalen Protokoll, deshalb läuft hier alles
ohne Netzwerk und ohne Zugangsdaten. Geprüft wird die Entscheidungslogik: Was
wird übertragen, was gelöscht, und vor allem — was bleibt unangetastet.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from src.bridge import BridgeConfig, load_config, run
from src.feed_reader import MANAGED_KEY, MANAGED_VALUE, FeedEvent, parse_feed
from src.google_calendar import sync_calendar

TZ = ZoneInfo("Europe/Berlin")


# ---------------------------------------------------------------------------
# Doubles
# ---------------------------------------------------------------------------


class FakeApi:
    """Merkt sich Aufrufe, statt Google zu fragen."""

    def __init__(self, existing: list[dict] | None = None) -> None:
        self.existing = list(existing or [])
        self.imported: list[dict] = []
        self.deleted: list[str] = []
        self.fail_import_for: set[str] = set()

    def list_managed(self, calendar_id, time_min):  # noqa: ARG002
        self.last_time_min = time_min
        return list(self.existing)

    def import_event(self, calendar_id, body):  # noqa: ARG002
        if body.get("summary") in self.fail_import_for:
            raise RuntimeError("Google mag diesen Termin nicht")
        self.imported.append(body)

    def delete_event(self, calendar_id, event_id):  # noqa: ARG002
        self.deleted.append(event_id)


def event(uid="hp-1", summary="U17 Heimspiel gegen Ratingen", day=3, hour=18, **kwargs) -> FeedEvent:
    start = datetime(2026, 10, day, hour, 15, tzinfo=TZ)
    defaults = {
        "uid": uid,
        "summary": summary,
        "start": start,
        "end": start + timedelta(hours=2),
        "all_day": False,
        "location": "Solingen",
    }
    defaults.update(kwargs)
    return FeedEvent(**defaults)


def google_item(ev: FeedEvent, event_id="g1") -> dict:
    """Wie Google einen von der Bridge angelegten Termin zurückliefert."""
    return {
        "id": event_id,
        "iCalUID": ev.uid,
        "summary": ev.summary,
        "location": ev.location,
        "start": {"dateTime": ev.start.isoformat()},
        "end": {"dateTime": ev.end.isoformat()},
    }


# ---------------------------------------------------------------------------
# Anlegen, Ändern, Löschen
# ---------------------------------------------------------------------------


class TestSyncCalendar:
    def test_neuer_termin_wird_uebertragen(self):
        api = FakeApi()
        report = sync_calendar(api, "cal", [event()])

        assert report.imported == 1
        assert api.imported[0]["iCalUID"] == "hp-1"

    def test_unveraenderter_termin_wird_nicht_neu_geschrieben(self):
        ev = event()
        api = FakeApi([google_item(ev)])
        report = sync_calendar(api, "cal", [ev])

        assert (report.imported, report.unchanged) == (0, 1)
        assert api.imported == []

    def test_verschobener_termin_wird_geaendert_statt_gedoppelt(self):
        alt = event(day=3)
        neu = event(day=21)  # gleiche UID, neues Datum
        api = FakeApi([google_item(alt)])

        report = sync_calendar(api, "cal", [neu])

        assert (report.imported, report.deleted) == (1, 0)
        assert api.deleted == []

    def test_geaenderter_titel_loest_uebertragung_aus(self):
        alt = event(summary="U17 Heimspiel gegen Ratingen")
        api = FakeApi([google_item(alt)])

        report = sync_calendar(api, "cal", [event(summary="U17 Heimspiel gegen Neuss")])
        assert report.imported == 1

    def test_entfallener_termin_wird_geloescht(self):
        api = FakeApi([google_item(event(), event_id="g9")])
        report = sync_calendar(api, "cal", [])

        assert report.deleted == 1
        assert api.deleted == ["g9"]

    def test_zweiter_lauf_aendert_nichts(self):
        """Der Idempotenz-Nachweis — der Kern der Umstellung."""
        ev = event()
        api = FakeApi([google_item(ev)])
        report = sync_calendar(api, "cal", [ev])

        assert report.changed == 0
        assert api.imported == [] and api.deleted == []


class TestFremdeTermineBleiben:
    def test_nur_markierte_termine_werden_gelistet(self):
        """Aufgeräumt wird ausschließlich in der eigenen Menge.

        Was jemand von Hand im Google-Kalender anlegt, taucht in
        ``list_managed`` gar nicht erst auf und kann deshalb nicht gelöscht
        werden. Der Filter dafür sitzt in der echten API-Klasse.
        """
        api = FakeApi([])  # Google liefert nur markierte Termine zurück
        report = sync_calendar(api, "cal", [])

        assert report.deleted == 0
        assert api.deleted == []

    def test_uebertragene_termine_tragen_die_markierung(self):
        api = FakeApi()
        sync_calendar(api, "cal", [event()])

        privat = api.imported[0]["extendedProperties"]["private"]
        assert privat == {MANAGED_KEY: MANAGED_VALUE}


class TestZeitvergleich:
    def test_abweichende_schreibweise_gilt_nicht_als_aenderung(self):
        """Google gibt Zeitstempel anders formatiert zurück als gesendet.

        Ein Textvergleich würde bei jedem Lauf eine Änderung melden und den
        Kalender endlos neu beschreiben.
        """
        ev = event()
        item = google_item(ev)
        item["start"]["dateTime"] = ev.start.astimezone(ZoneInfo("UTC")).isoformat()
        item["end"]["dateTime"] = ev.end.astimezone(ZoneInfo("UTC")).isoformat()

        report = sync_calendar(FakeApi([item]), "cal", [ev])
        assert report.unchanged == 1

    def test_ganztaegiger_termin_wird_als_datum_uebertragen(self):
        ev = event(all_day=True, location="")
        api = FakeApi()
        sync_calendar(api, "cal", [ev])

        assert "date" in api.imported[0]["start"]
        assert "dateTime" not in api.imported[0]["start"]


class TestFehlerToleranz:
    def test_ein_kaputter_termin_kippt_den_lauf_nicht(self):
        api = FakeApi()
        api.fail_import_for = {"U17 Heimspiel gegen Ratingen"}

        report = sync_calendar(api, "cal", [event(), event(uid="hp-2", summary="U17 Training")])

        assert report.imported == 1
        assert len(report.errors) == 1
        assert "Ratingen" in report.errors[0]


class TestProbelauf:
    def test_dry_run_schreibt_nichts_meldet_aber_dasselbe(self):
        api = FakeApi([google_item(event(uid="alt"), event_id="g1")])
        report = sync_calendar(api, "cal", [event(uid="neu")], dry_run=True)

        assert (report.imported, report.deleted) == (1, 1)
        assert api.imported == [] and api.deleted == []


# ---------------------------------------------------------------------------
# Konfiguration und Ablauf
# ---------------------------------------------------------------------------


class TestLoadConfig:
    def test_liest_kalender_und_schluesselpfad(self):
        config = load_config(
            {
                "ECB_CALENDARS": json.dumps({"U17": "abc@group.calendar.google.com"}),
                "GOOGLE_APPLICATION_CREDENTIALS": "/secrets/key.json",
            }
        )

        assert config.calendars == {"U17": "abc@group.calendar.google.com"}
        assert config.feed_url("U17").endswith("/u17.ics")

    def test_fehlende_kalender_melden_das_erwartete_format(self):
        with pytest.raises(ValueError, match="ECB_CALENDARS"):
            load_config({"GOOGLE_APPLICATION_CREDENTIALS": "/k.json"})

    def test_kaputtes_json_wird_benannt(self):
        with pytest.raises(ValueError, match="JSON"):
            load_config(
                {"ECB_CALENDARS": "{kein json", "GOOGLE_APPLICATION_CREDENTIALS": "/k.json"}
            )

    def test_fehlender_schluessel_wird_benannt(self):
        with pytest.raises(ValueError, match="GOOGLE_APPLICATION_CREDENTIALS"):
            load_config({"ECB_CALENDARS": json.dumps({"U17": "x"})})


class TestRun:
    def _config(self):
        return BridgeConfig(
            feed_base="http://kalender:3000/feeds",
            key_file="/secrets/key.json",
            calendars={"U17": "cal-u17", "U13": "cal-u13"},
        )

    def test_gleicht_alle_konfigurierten_kalender_ab(self):
        api = FakeApi()
        reports = run(self._config(), api, loader=lambda url: [event()])

        assert [r.calendar for r in reports] == ["U17", "U13"]

    def test_einzelnes_team_moeglich(self):
        api = FakeApi()
        reports = run(self._config(), api, teams=["U17"], loader=lambda url: [event()])

        assert len(reports) == 1

    def test_nicht_abrufbarer_feed_laesst_den_kalender_unveraendert(self):
        """Ein leerer Feed sähe aus wie „alle Termine entfallen".

        Die Bridge würde den Kalender leerräumen. Deshalb wird ein Team mit
        kaputtem Feed übersprungen statt mit leerer Liste abgeglichen.
        """
        api = FakeApi([google_item(event(), event_id="g1")])

        def kaputt(url):
            raise OSError("Server nicht erreichbar")

        reports = run(self._config(), api, teams=["U17"], loader=kaputt)

        assert reports == []
        assert api.deleted == []


# ---------------------------------------------------------------------------
# Feed einlesen
# ---------------------------------------------------------------------------


FEED = """BEGIN:VCALENDAR\r
VERSION:2.0\r
PRODID:-//ECB//Kalenderview//DE\r
BEGIN:VEVENT\r
UID:hp-heim-1@ecb-kalenderview\r
DTSTAMP:20260812T120000Z\r
DTSTART:20261003T161500Z\r
DTEND:20261003T183000Z\r
SUMMARY:U17 Heimspiel gegen Ratingen\r
LOCATION:Solingen\r
END:VEVENT\r
END:VCALENDAR\r
"""


class TestParseFeed:
    def test_liest_termine_mit_uid_und_titel(self):
        events = parse_feed(FEED)

        assert len(events) == 1
        assert events[0].uid == "hp-heim-1@ecb-kalenderview"
        assert events[0].summary == "U17 Heimspiel gegen Ratingen"
        assert events[0].location == "Solingen"

    def test_rechnet_in_lokale_zeit_um(self):
        # 16:15 UTC im Oktober sind 18:15 in Berlin.
        events = parse_feed(FEED)
        assert events[0].start.hour == 18

    def test_leerer_kalender_ergibt_leere_liste(self):
        leer = "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//x//x//DE\r\nEND:VCALENDAR\r\n"
        assert parse_feed(leer) == []


class TestFetchFeed:
    def test_sendet_eigene_kennung_statt_python_urllib(self):
        """Cloudflare blockt ``Python-urllib`` mit Fehler 1010."""
        from src.feed_reader import USER_AGENT, fetch_feed

        gesehen = []

        class _Antwort:
            def read(self):
                return b"BEGIN:VCALENDAR\r\nEND:VCALENDAR\r\n"

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

        def opener(request, timeout=None):  # noqa: ARG001
            gesehen.append(request)
            return _Antwort()

        fetch_feed("https://kalender.example/feeds/u17.ics", opener=opener)

        agent = gesehen[0].get_header("User-agent")
        assert agent == USER_AGENT
        assert "Python-urllib" not in agent
