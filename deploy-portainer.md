# Bridge über Portainer deployen

Die Bridge läuft als **eigener Stack** neben dem Kalenderview-Stack. Diese
Anleitung ist für die **Testumgebung auf der Synology** geschrieben; für den
späteren Produktivserver in der Eishalle gilt sie unverändert, nur mit anderen
Pfaden und anderer Portainer-Instanz (siehe [Später: Eishallen-Server](#später-eishallen-server)).

> **Zum Testen gilt eine Regel über allen anderen:** In `ECB_CALENDARS` steht
> **nur der Wegwerf-Kalender**. Die zehn produktiven Kalender kommen erst rein,
> wenn ein Lauf und ein Wiederholungslauf sauber durchgelaufen sind.

## Voraussetzungen

- Kalenderview läuft bereits als Stack (siehe `deploy/portainer-synology.md`
  im Kalenderview-Repo) und ist auf dem Stand mit den `/feeds`-Endpunkten
- Das Google-Dienstkonto ist eingerichtet und die Schlüsseldatei liegt vor
- Ein **Wegwerf-Kalender** in Google, für die Dienstkonto-Adresse freigegeben

## 1. Schlüsseldatei auf die Synology legen

Über File Station in einen Ordner, der **nicht** freigegeben ist:

```
/volume1/docker/ecb-bridge/secrets/ecb-bridge-key.json
```

Die Datei ist ein dauerhaftes Passwort — sie gehört weder in ein Repository
noch in ein Abbild und wird unten nur lesend eingehängt.

## 2. Netznamen des Kalenderview-Stacks feststellen

Portainer → **Networks**. Gesucht ist das Netz des Kalenderview-Stacks; es
heißt nach dem Stack, typischerweise `eisbelegungsplan_default`. Den genauen
Namen notieren.

Alternative, falls das nicht klappt: Schritt 3 mit
`ECB_FEED_BASE=http://<NAS-IP>:3050/feeds` und ohne geteiltes Netz. Dann läuft
der Verkehr über den Host — für einen Test völlig ausreichend.

## 3. Stack anlegen

Portainer → **Stacks** → **Add stack** → **Repository**

| Feld | Wert |
|---|---|
| Name | `ecb-kalender-bridge` |
| Repository URL | `https://github.com/mirco71/excel2IcsCalender` |
| Repository reference | `refs/heads/main` |
| Compose path | `docker-compose.bridge.yml` |
| Authentication | GitHub-PAT wie beim Kalenderview-Stack |

**Environment variables:**

| Variable | Wert |
|---|---|
| `ECB_CALENDARS` | `{"U17": "<ID-des-Wegwerf-Kalenders>"}` |
| `ECB_KEY_FILE` | `/volume1/docker/ecb-bridge/secrets/ecb-bridge-key.json` |
| `ECB_NETWORK` | Netzname aus Schritt 2 |
| `ECB_FEED_BASE` | nur setzen, wenn ohne geteiltes Netz gearbeitet wird |

Deploy.

## 4. Erster Lauf — Probelauf

Der Container startet im Dauerbetrieb (alle 15 Minuten). Für einen kontrollierten
ersten Lauf zuerst trocken:

```bash
docker exec ecb-kalender-bridge python -m src.bridge --dry-run
```

Erwartet: eine Zeile je Team mit der Anzahl. Es darf nichts geschrieben werden.

**Wenn hier schon etwas klemmt**, siehe [Troubleshooting](#troubleshooting) —
die häufigsten Fälle sind der Netzname und der Pfad zur Schlüsseldatei.

## 5. Echter Lauf und der eigentliche Beweis

```bash
docker exec ecb-kalender-bridge python -m src.bridge
docker exec ecb-kalender-bridge python -m src.bridge
```

Der **zweite** Aufruf muss `0 übertragen, 0 gelöscht` melden. Das ist der
Nachweis, dass der Abgleich wiederholbar ist und nicht bei jedem Lauf alles neu
schreibt — genau der Fehler des alten `clear_n_update.py`.

Danach im Google-Kalender nachsehen: Termine da, Zeiten richtig, keine
Dubletten.

## 6. Laufenden Betrieb prüfen

```bash
docker logs -f ecb-kalender-bridge
```

Alle 15 Minuten eine Zusammenfassung je Team. Im Normalbetrieb steht dort
`0 übertragen, 0 gelöscht` — Änderungen erscheinen nur, wenn sich in
Kalenderview wirklich etwas geändert hat.

## Später: Eishallen-Server

Derselbe Stack, dieselben Schritte. Zu ändern sind:

- **Pfad der Schlüsseldatei** (`ECB_KEY_FILE`), z.B. `/opt/ecb/secrets/…`
- **Netzname** (`ECB_NETWORK`), falls der Kalenderview-Stack dort anders heißt
- **`ECB_CALENDARS`** auf alle zehn produktiven Kalender

Die Schlüsseldatei muss auf dem neuen Server erneut abgelegt werden; sie wandert
nicht mit dem Stack mit. Alternativ lässt sich in der Cloud Console ein zweiter
Schlüssel für dasselbe Dienstkonto erzeugen, dann kann der alte nach dem Umzug
gelöscht werden.

## Troubleshooting

| Problem | Ursache |
|---|---|
| `network … not found` beim Deploy | `ECB_NETWORK` stimmt nicht — Name unter Portainer → Networks nachsehen |
| `Dienstkonto-Schluesseldatei nicht gefunden` | `ECB_KEY_FILE` zeigt ins Leere, oder die Datei ist für den Docker-Nutzer nicht lesbar |
| `Feed … nicht abrufbar` | Kalenderview nicht erreichbar. Mit geteiltem Netz `http://ecb-kalender:3000/feeds`, sonst Host-IP und Port 3050 |
| `404` auf einen Team-Feed | Das Team-Kürzel ist keines der bekannten (`U7 U9 U11 U13 U15 U17 U20 Damen Senioren Goalies`) |
| `403` von Google | Der Kalender ist nicht für das Dienstkonto freigegeben, oder mit zu schwachem Recht |
| Kalender bleibt leer, keine Fehlermeldung | Feed liefert keine Termine — in Kalenderview nachsehen, ob überhaupt welche für dieses Team da sind |
