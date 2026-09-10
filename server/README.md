# Lokales Frontend (optional)

Zeigt README, Grobübersicht, Module, Proposals, Entscheidungs-Log, die
lokale Commit-Historie ("was Agenten zuletzt geschrieben haben") und
einen **Live-Banner** ("Woran Agenten JETZT arbeiten") auf einer
einzigen Seite - läuft nur auf diesem Rechner, keine öffentliche Adresse.

Einziger Schreibzugriff: der Check-in-Endpunkt (`POST /api/checkin`) für
den Live-Banner - reine Statusmeldung, kein Steuerungsmechanismus.
Ansonsten rein lesend. GitHub bleibt die kanonische Quelle für Code.

Bleibt dauerhaft aktuell, solange der Server läuft: er zieht im
Hintergrund alle 30s automatisch `git pull`, und die Seite lädt sich
selbst alle 10s neu. Kein manuelles Eingreifen nötig.

## Start

```bash
git pull            # einmalig: lokalen Checkout anlegen/aktuell halten
python3 server/serve.py
```

Danach im Browser öffnen:

```
http://127.0.0.1:8765/
```

## Live-Banner: Agenten checken ein

Agenten melden ihren aktuellen Status (siehe
[docs/AGENT_PROMPT.md](../docs/AGENT_PROMPT.md) für den vollen Ablauf):

```bash
curl -s -X POST http://127.0.0.1:8765/api/checkin \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"sonnet-a","status":"baut Modul X","detail":"schreibt Tests"}'
```

Ein Check-in gilt nach 15 Minuten ohne Update als "inaktiv" (grauer statt
grüner Punkt im Banner), verschwindet aber nicht - so sieht man auch, wer
zuletzt woran gearbeitet hat.

## Einzelne Dateien direkt abrufen

Für Agenten, die gezielt nur eine Datei lesen wollen statt das ganze Repo:

```
http://127.0.0.1:8765/project/README.md
http://127.0.0.1:8765/project/OVERVIEW.md
http://127.0.0.1:8765/project/modules/<name>/OVERVIEW.md
```

## Weitere Endpunkte

- `http://127.0.0.1:8765/api/status` - aktuelle Check-ins (JSON)
- `http://127.0.0.1:8765/api/sync` - Status des automatischen `git pull`
- `http://127.0.0.1:8765/api/activity` - letzte 20 Commits (JSON)

Anderer Port: `python3 server/serve.py 9000`.
