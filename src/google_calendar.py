"""Abgleich eines Feeds gegen einen Google-Kalender.

Der alte Weg (``clear_n_update.py``) hat bei jedem Lauf **alle** Termine
gelöscht und neu angelegt. Das hatte drei Nachteile: Abonnenten sahen jedes Mal
sämtliche Termine als neu, ein abgebrochener Lauf hinterließ einen halb leeren
Kalender, und von Hand ergänzte Termine gingen mit verloren.

Hier wird stattdessen gezielt abgeglichen. Zwei Dinge machen das möglich:

* **``iCalUID``** — der stabile Schlüssel aus Hallenplanung. Google nutzt ihn
  beim Import als Identität, ein verschobener Termin wird also geändert.
* **``extendedProperties.private.ecb_bridge``** — die Markierung, dass ein
  Termin von der Bridge stammt. Aufgeräumt wird ausschließlich in dieser Menge.

Die Google-API steckt hinter einem schmalen Protokoll (:class:`EventsApi`),
damit die Entscheidungslogik ohne Netzwerk und ohne Zugangsdaten geprüft werden
kann — dort sitzen die Fehler, die wehtun.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Protocol

from src.feed_reader import MANAGED_KEY, MANAGED_VALUE, TIMEZONE, FeedEvent

#: Wie weit zurück die Bridge Termine verwaltet. Alles davor bleibt liegen —
#: alte Saisons sollen nicht plötzlich verschwinden, nur weil sie nicht mehr im
#: Feed stehen.
DEFAULT_PAST_DAYS = 30


class EventsApi(Protocol):
    """Der Ausschnitt der Google-Calendar-API, den die Bridge braucht."""

    def list_managed(self, calendar_id: str, time_min: str) -> list[dict]: ...

    def import_event(self, calendar_id: str, body: dict) -> None: ...

    def delete_event(self, calendar_id: str, event_id: str) -> None: ...


@dataclass
class SyncReport:
    """Was ein Abgleich bewirkt hat — für Protokoll und Tests."""

    calendar: str
    imported: int = 0
    deleted: int = 0
    unchanged: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def changed(self) -> int:
        return self.imported + self.deleted

    def summary(self) -> str:
        text = (
            f"{self.calendar}: {self.imported} übertragen, "
            f"{self.deleted} gelöscht, {self.unchanged} unverändert"
        )
        if self.errors:
            text += f", {len(self.errors)} Fehler"
        return text


def _time_min(past_days: int, now: datetime | None = None) -> str:
    """Untergrenze für ``events.list`` als RFC-3339-Zeitstempel."""
    reference = now or datetime.now(TIMEZONE)
    return (reference - timedelta(days=past_days)).isoformat()


def _needs_update(existing: dict, wanted: FeedEvent) -> bool:
    """Prüft, ob sich der Google-Termin vom Feed unterscheidet.

    Verglichen wird nur, was die Bridge selbst setzt. Alles andere — etwa eine
    Erinnerung, die jemand am Termin eingestellt hat — bleibt unangetastet und
    darf keinen Schreibvorgang auslösen.
    """
    if (existing.get("summary") or "") != wanted.summary:
        return True
    if (existing.get("location") or "") != wanted.location:
        return True

    start = existing.get("start") or {}
    end = existing.get("end") or {}
    if wanted.all_day:
        return (
            start.get("date") != wanted.start.date().isoformat()
            or end.get("date") != wanted.end.date().isoformat()
        )

    return not (
        _same_moment(start.get("dateTime"), wanted.start)
        and _same_moment(end.get("dateTime"), wanted.end)
    )


def _same_moment(raw: str | None, expected: datetime) -> bool:
    """Vergleicht Zeitpunkte, nicht Schreibweisen.

    Google gibt Zeitstempel in eigener Formatierung zurück (etwa mit ``+02:00``
    statt der gesendeten Zone). Ein Textvergleich würde deshalb bei jedem Lauf
    eine Änderung melden und den Kalender unnötig neu beschreiben.
    """
    if not raw:
        return False
    try:
        return datetime.fromisoformat(raw) == expected
    except ValueError:
        return False


def sync_calendar(
    api: EventsApi,
    calendar_id: str,
    events: list[FeedEvent],
    *,
    label: str | None = None,
    past_days: int = DEFAULT_PAST_DAYS,
    dry_run: bool = False,
    now: datetime | None = None,
) -> SyncReport:
    """Gleicht einen Google-Kalender gegen die Termine eines Feeds ab.

    Angefasst werden ausschließlich Termine mit der Bridge-Markierung ab
    ``past_days`` in der Vergangenheit. Was jemand von Hand im Kalender angelegt
    hat, bleibt unberührt — genauso wie manuelle Termine in Kalenderview vom
    dortigen Abgleich unberührt bleiben.

    Ein Fehler an einem einzelnen Termin bricht den Lauf nicht ab: Die übrigen
    werden weiter abgeglichen und der Fehler im Bericht vermerkt. Ein
    Kalenderausfall wegen eines einzigen kaputten Termins wäre schlimmer als
    ein unvollständiger Lauf.
    """
    report = SyncReport(calendar=label or calendar_id)

    existing = api.list_managed(calendar_id, _time_min(past_days, now))
    by_uid: dict[str, dict] = {}
    for item in existing:
        uid = item.get("iCalUID")
        if uid:
            by_uid[uid] = item

    wanted_uids = set()
    for event in events:
        wanted_uids.add(event.uid)
        current = by_uid.get(event.uid)
        if current is not None and not _needs_update(current, event):
            report.unchanged += 1
            continue
        if dry_run:
            report.imported += 1
            continue
        try:
            api.import_event(calendar_id, event.google_body())
            report.imported += 1
        except Exception as exc:  # noqa: BLE001 — ein Termin darf den Lauf nicht kippen
            report.errors.append(f"{event.summary}: {exc}")

    for uid, item in by_uid.items():
        if uid in wanted_uids:
            continue
        if dry_run:
            report.deleted += 1
            continue
        try:
            api.delete_event(calendar_id, item["id"])
            report.deleted += 1
        except Exception as exc:  # noqa: BLE001
            report.errors.append(f"Löschen {item.get('summary', uid)}: {exc}")

    return report


# ---------------------------------------------------------------------------
# Echte Google-Anbindung
# ---------------------------------------------------------------------------


class GoogleEventsApi:
    """:class:`EventsApi` auf Basis des offiziellen Google-Clients.

    Die Anmeldung läuft über ein **Dienstkonto**: kein Browser, kein
    Consent-Fenster, kein ablaufendes Token — nötig, weil die Bridge in einem
    Container ohne Bildschirm läuft. Der Zugriff kommt daher, dass jeder
    Kalender für die Dienstkonto-Adresse freigegeben wurde.
    """

    SCOPES = ["https://www.googleapis.com/auth/calendar"]

    def __init__(self, service) -> None:
        self._service = service

    @classmethod
    def from_service_account(cls, key_file: str) -> GoogleEventsApi:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        credentials = service_account.Credentials.from_service_account_file(
            key_file, scopes=cls.SCOPES
        )
        return cls(build("calendar", "v3", credentials=credentials, cache_discovery=False))

    def list_managed(self, calendar_id: str, time_min: str) -> list[dict]:
        items: list[dict] = []
        page_token = None
        while True:
            response = (
                self._service.events()
                .list(
                    calendarId=calendar_id,
                    timeMin=time_min,
                    # Nur die eigenen Termine — fremde bleiben unsichtbar und
                    # damit vom Aufräumen ausgenommen.
                    privateExtendedProperty=f"{MANAGED_KEY}={MANAGED_VALUE}",
                    singleEvents=True,
                    showDeleted=False,
                    maxResults=2500,
                    pageToken=page_token,
                )
                .execute()
            )
            items.extend(response.get("items", []))
            page_token = response.get("nextPageToken")
            if not page_token:
                break
        return items

    def import_event(self, calendar_id: str, body: dict) -> None:
        # ``import_`` statt ``import`` — letzteres ist ein Python-Schlüsselwort.
        # Der Aufruf legt anhand der iCalUID an oder aktualisiert.
        self._service.events().import_(calendarId=calendar_id, body=body).execute()

    def delete_event(self, calendar_id: str, event_id: str) -> None:
        self._service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
