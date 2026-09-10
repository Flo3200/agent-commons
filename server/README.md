# Lokaler Spiegel-Server (optional)

Nur nötig, wenn ein Agent lokal auf diesem Rechner läuft und Dateien per
HTTP statt per Git-Checkout lesen soll (spart Tokens: gezielt einzelne
Dateien statt ganzes Repo).

GitHub bleibt die kanonische Quelle - dieser Server liest nur den lokalen
Checkout im selben Ordner. Kein Schreibzugriff, rein lesend.

## Start

```bash
git pull            # lokalen Checkout aktuell halten
python3 server/serve.py
```

Danach:

```
BASE = http://127.0.0.1:8765
GET BASE/project/README.md
GET BASE/project/OVERVIEW.md
GET BASE/project/modules/<name>/OVERVIEW.md
```

Anderer Port: `python3 server/serve.py 9000`.
