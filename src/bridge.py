"""ECB Kalender-Bridge: Kalenderview → Google-Kalender.

Holt für jedes Team den öffentlichen iCalendar-Feed aus Kalenderview und gleicht
ihn gegen den zugehörigen Google-Kalender ab. Läuft als Container im
Portainer-Stack neben Kalenderview und spricht es über das interne Docker-Netz
an.

Aufruf::

    python -m src.bridge                 # alle konfigurierten Kalender
    python -m src.bridge --dry-run       # nur anzeigen, nichts schreiben
    python -m src.bridge --team U17      # nur ein Team

Konfiguration über Umgebungsvariablen (siehe :func:`load_config`), damit im
Container nichts im Abbild liegt.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from dataclasses import dataclass

from src.feed_reader import FeedEvent, load_feed
from src.google_calendar import DEFAULT_PAST_DAYS, EventsApi, GoogleEventsApi, sync_calendar

LOG = logging.getLogger("bridge")

DEFAULT_FEED_BASE = "http://ecb-kalender:3000/feeds"


@dataclass(frozen=True)
class BridgeConfig:
    """Alles, was ein Lauf braucht."""

    feed_base: str
    key_file: str
    #: ``{"U17": "…@group.calendar.google.com", …}``
    calendars: dict[str, str]
    past_days: int = DEFAULT_PAST_DAYS

    def feed_url(self, team: str) -> str:
        return f"{self.feed_base.rstrip('/')}/{team.lower()}.ics"


def load_config(env: dict | None = None) -> BridgeConfig:
    """Liest die Konfiguration aus der Umgebung.

    ``ECB_CALENDARS`` ist ein JSON-Objekt Team → Kalender-ID. Als Datei statt
    als Variable wäre es im Container umständlicher zu setzen; die IDs sind
    keine Geheimnisse, der Dienstkonto-Schlüssel dagegen schon — der kommt
    deshalb als Pfad auf eine eingehängte Datei.
    """
    source = env if env is not None else os.environ

    raw = source.get("ECB_CALENDARS", "").strip()
    if not raw:
        raise ValueError(
            "ECB_CALENDARS fehlt — erwartet ein JSON-Objekt, z.B. "
            '{"U17": "abc@group.calendar.google.com"}'
        )
    try:
        calendars = json.loads(raw)
    except ValueError as exc:
        raise ValueError(f"ECB_CALENDARS ist kein gültiges JSON: {exc}") from exc
    if not isinstance(calendars, dict) or not calendars:
        raise ValueError("ECB_CALENDARS muss ein nicht-leeres JSON-Objekt sein")

    key_file = source.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    if not key_file:
        raise ValueError(
            "GOOGLE_APPLICATION_CREDENTIALS fehlt — Pfad auf die "
            "Dienstkonto-Schlüsseldatei erwartet"
        )

    return BridgeConfig(
        feed_base=source.get("ECB_FEED_BASE", DEFAULT_FEED_BASE).strip(),
        key_file=key_file,
        calendars={str(k): str(v) for k, v in calendars.items()},
        past_days=int(source.get("ECB_PAST_DAYS", DEFAULT_PAST_DAYS)),
    )


def run(
    config: BridgeConfig,
    api: EventsApi,
    *,
    teams: list[str] | None = None,
    dry_run: bool = False,
    loader=load_feed,
) -> list:
    """Gleicht alle konfigurierten Kalender ab und gibt die Berichte zurück.

    Ein Team, dessen Feed sich nicht laden lässt, wird **übersprungen** statt
    abgeglichen: Ein leerer Feed sähe aus wie „alle Termine entfallen" und die
    Bridge würde den Kalender leerräumen. Lieber ein Lauf ohne Änderung als ein
    geleerter Kalender.
    """
    selected = teams or list(config.calendars)
    reports = []

    for team in selected:
        calendar_id = config.calendars.get(team)
        if calendar_id is None:
            LOG.warning("Kein Kalender für Team %s konfiguriert — übersprungen", team)
            continue

        url = config.feed_url(team)
        try:
            events: list[FeedEvent] = loader(url)
        except Exception as exc:  # noqa: BLE001 — siehe Docstring
            LOG.error("Feed %s nicht abrufbar (%s) — Kalender bleibt unverändert", url, exc)
            continue

        report = sync_calendar(
            api,
            calendar_id,
            events,
            label=team,
            past_days=config.past_days,
            dry_run=dry_run,
        )
        reports.append(report)
        LOG.info("%s", report.summary())
        for error in report.errors:
            LOG.error("  %s", error)

    return reports


def main(argv: list[str] | None = None) -> int:
    # Beschreibung und Hilfetexte bewusst ohne Sonderzeichen jenseits von
    # Latin-1: Die Windows-Konsole nutzt cp1252, und ein Pfeil "→" lässt
    # `--help` dort mit einem UnicodeEncodeError abstürzen.
    parser = argparse.ArgumentParser(
        description="ECB Kalender-Bridge: Termine von Kalenderview nach Google uebertragen"
    )
    parser.add_argument("--dry-run", action="store_true", help="nur anzeigen, nichts schreiben")
    parser.add_argument("--team", action="append", help="nur dieses Team (mehrfach möglich)")
    parser.add_argument("--verbose", action="store_true", help="ausführliche Ausgabe")
    parser.add_argument(
        "--interval",
        type=int,
        default=0,
        help="Sekunden zwischen zwei Läufen; 0 = einmal ausführen (Vorgabe)",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(message)s",
    )

    try:
        config = load_config()
    except ValueError as exc:
        LOG.error("Konfiguration unvollständig: %s", exc)
        return 2

    if not os.path.isfile(config.key_file):
        # Der häufigste Startfehler im Container: Der Mount zeigt ins Leere.
        # Ein roher FileNotFoundError-Traceback hilft dabei niemandem weiter.
        LOG.error(
            "Dienstkonto-Schluesseldatei nicht gefunden: %s. "
            "Pfad und Volume-Einhaengung pruefen.",
            config.key_file,
        )
        return 2

    api = GoogleEventsApi.from_service_account(config.key_file)

    if args.interval <= 0:
        return _one_run(config, api, args)

    # Dauerbetrieb im Container. Bewusst eine Schleife statt cron: So gibt es
    # nur einen Prozess, ein Protokoll und eine Fehlerbehandlung. Ein
    # fehlgeschlagener Lauf beendet den Dienst nicht — beim nächsten Durchgang
    # kann der Server längst wieder erreichbar sein.
    LOG.info("Dauerbetrieb: Abgleich alle %s Sekunden", args.interval)
    while True:
        try:
            _one_run(config, api, args)
        except Exception:  # noqa: BLE001 — der Dienst soll weiterlaufen
            LOG.exception("Lauf abgebrochen — nächster Versuch in %s Sekunden", args.interval)
        time.sleep(args.interval)


def _one_run(config: BridgeConfig, api: EventsApi, args) -> int:
    reports = run(config, api, teams=args.team, dry_run=args.dry_run)

    if not reports:
        LOG.warning("Kein Kalender abgeglichen")
        return 1

    geaendert = sum(r.changed for r in reports)
    fehler = sum(len(r.errors) for r in reports)
    LOG.info("Fertig: %s Änderungen, %s Fehler", geaendert, fehler)
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
