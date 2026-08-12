# ECB Kalender-Bridge: Kalenderview → Google-Kalender
#
# Läuft als Dienst im selben Portainer-Stack wie Kalenderview und spricht es
# über das interne Docker-Netz an. Der Dienstkonto-Schlüssel wird als Datei
# eingehängt und liegt bewusst NICHT im Abbild.

FROM python:3.12-slim

# Zeitzone festnageln: Der Feed liefert Zeiten mit Zonenangabe, aber Protokoll
# und Zeitfenster-Berechnung sollen in Ortszeit lesbar sein — wie beim
# Kalenderview-Container auch.
ENV TZ=Europe/Berlin \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Nur die Bridge-Abhängigkeiten. pandas und openpyxl gehören zum Alt-Weg
# Excel → ICS und werden hier nicht gebraucht — sie würden das Abbild ohne
# Gegenwert um ein Vielfaches aufblähen.
COPY requirements-bridge.txt ./
RUN pip install --no-cache-dir -r requirements-bridge.txt

COPY src/ ./src/

# Vorgabe: alle 15 Minuten. Eine Absage in Kalenderview ist damit spätestens
# nach einer Viertelstunde aus den Google-Kalendern verschwunden.
CMD ["python", "-m", "src.bridge", "--interval", "900"]
