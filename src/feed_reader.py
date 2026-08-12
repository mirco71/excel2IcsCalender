"""Liest die öffentlichen iCalendar-Feeds von Kalenderview.

Die Bridge holt ihre Daten bewusst über dieselben Feeds, die auch die Handys
abonnieren: Damit braucht sie gegenüber Kalenderview keine Anmeldung, und der
Feed wird durch den Dauerbetrieb der Bridge nebenbei mitgetestet. Weicht er
kaputt ab, fällt es hier auf, bevor sich Eltern wundern.

Ergebnis sind :class:`FeedEvent`-Objekte — bewusst eine eigene, schlanke Form
statt der Objekte der ``ics``-Bibliothek, damit der Abgleich in
:mod:`src.google_calendar` ohne deren Eigenheiten auskommt und ohne Netzwerk
testbar bleibt.
"""

from __future__ import annotations

import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from ics import Calendar

TIMEZONE = ZoneInfo("Europe/Berlin")
DEFAULT_TIMEOUT = 30.0


@dataclass(frozen=True)
class FeedEvent:
    """Ein Termin aus dem Feed, reduziert auf das für Google Nötige."""

    uid: str
    summary: str
    start: datetime
    end: datetime
    all_day: bool
    location: str = ""

    def google_body(self) -> dict:
        """Baut den Google-Termin.

        ``iCalUID`` ist der Angelpunkt des ganzen Abgleichs: Google nutzt ihn
        beim Import als Schlüssel, sodass ein verschobenes Spiel geändert und
        nicht ein zweites Mal angelegt wird.

        ``extendedProperties.private`` markiert den Termin als von der Bridge
        verwaltet. Nur solche Termine löscht sie später wieder — was jemand von
        Hand im Kalender anlegt, bleibt unangetastet.
        """
        if self.all_day:
            start = {"date": self.start.date().isoformat()}
            end = {"date": self.end.date().isoformat()}
        else:
            start = {"dateTime": self.start.isoformat(), "timeZone": str(TIMEZONE)}
            end = {"dateTime": self.end.isoformat(), "timeZone": str(TIMEZONE)}

        body = {
            "iCalUID": self.uid,
            "summary": self.summary,
            "start": start,
            "end": end,
            "extendedProperties": {"private": {MANAGED_KEY: MANAGED_VALUE}},
        }
        if self.location:
            body["location"] = self.location
        return body


#: Markierung an jedem von der Bridge angelegten Google-Termin. Ohne sie könnte
#: der Abgleich nicht zwischen „von uns" und „von Hand angelegt" unterscheiden
#: und würde beim Aufräumen fremde Termine löschen.
MANAGED_KEY = "ecb_bridge"
MANAGED_VALUE = "1"


def fetch_feed(url: str, *, timeout: float = DEFAULT_TIMEOUT, opener=None) -> str:
    """Lädt einen Feed als Text. ``opener`` ist der Einstiegspunkt für Tests."""
    open_url = opener or urllib.request.urlopen
    with open_url(url, timeout=timeout) as response:
        return response.read().decode("utf-8")


def parse_feed(text: str) -> list[FeedEvent]:
    """Wandelt einen iCalendar-Text in :class:`FeedEvent`-Objekte.

    Termine ohne UID werden übersprungen: Ohne stabilen Schlüssel könnte der
    Abgleich sie bei jedem Lauf nur löschen und neu anlegen — genau das
    Verhalten, das mit der Umstellung verschwinden soll.
    """
    calendar = Calendar(text)
    events: list[FeedEvent] = []

    for event in calendar.events:
        if not event.uid:
            continue

        start = event.begin.datetime
        end = event.end.datetime if event.end else start + timedelta(hours=1)
        all_day = bool(getattr(event, "all_day", False))

        events.append(
            FeedEvent(
                uid=str(event.uid),
                summary=str(event.name or "").strip(),
                start=start.astimezone(TIMEZONE) if not all_day else start,
                end=end.astimezone(TIMEZONE) if not all_day else end,
                all_day=all_day,
                location=str(event.location or "").strip(),
            )
        )

    events.sort(key=lambda e: (e.start, e.uid))
    return events


def load_feed(url: str, *, timeout: float = DEFAULT_TIMEOUT, opener=None) -> list[FeedEvent]:
    """Holt und zerlegt einen Feed in einem Schritt."""
    return parse_feed(fetch_feed(url, timeout=timeout, opener=opener))
