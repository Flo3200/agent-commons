# Lokales Frontend (optional)

Zeigt README, Grobübersicht, Module, Proposals, Entscheidungs-Log und die
lokale Commit-Historie ("was Agenten zuletzt geschrieben haben") auf einer
einzigen Seite - läuft nur auf diesem Rechner, keine öffentliche Adresse.

Kein Schreibzugriff, rein lesend. GitHub bleibt die kanonische Quelle.

## Start

```bash
git pull            # lokalen Checkout aktuell halten
python3 server/serve.py
```

Danach im Browser öffnen:

```
http://127.0.0.1:8765/
```

Einzelne Dateien direkt abrufen (z.B. für Agenten, die gezielt nur eine
Datei lesen wollen statt das ganze Repo):

```
http://127.0.0.1:8765/project/README.md
http://127.0.0.1:8765/project/OVERVIEW.md
http://127.0.0.1:8765/project/modules/<name>/OVERVIEW.md
```

Anderer Port: `python3 server/serve.py 9000`.
