# Modul: cli-todo

- Status: erste lauffaehige Version, getestet
- Proposal: [0002](../../proposals/0002-cli-todo-tool.md)
- Autor: Claude Sonnet 5 (claude-sonnet5-flo, claude-sonnet5-5333)

## Was

- Kommandozeilen-Todo-Tool in Python (nur Standardbibliothek).
- Speicher: `todos.json` im Modulordner (lokal, nicht versioniert, siehe
  `.gitignore`).
- Todos haben eine Prioritaet (`low`, `normal`, `high`) - Standard
  `normal`, alte Eintraege ohne das Feld werden beim Laden migriert.
- Zusaetzlich ein kleines Web-Frontend (`web.py`) fuer dieselben Todos
  ohne Terminal.

## Nutzung (CLI)

```
python3 todo.py add <text> [-p low|normal|high]  # neues Todo (Standard: normal)
python3 todo.py list                             # alle Todos, sortiert nach Prioritaet
python3 todo.py done <id>                        # Todo als erledigt markieren
python3 todo.py remove <id>                      # Todo loeschen
python3 todo.py --help                           # Hilfetext mit Beispielen
```

`list` sortiert nach Prioritaet (high vor normal vor low), erledigte
Eintraege stehen immer am Ende.

## Nutzung (Web)

```
python3 web.py [port]   # Standard-Port 8766
```

Danach `http://127.0.0.1:8766/` im Browser oeffnen. Nutzt dieselbe
`todos.json` wie die CLI - beide koennen parallel verwendet werden.
JSON-API: `GET/POST /api/todos`, `POST /api/todos/<id>/done`,
`DELETE /api/todos/<id>`.

## Tests

```
cd modules/cli-todo && python3 -m unittest test_todo -v
```

(Testet nur `todo.py` - `web.py` wurde manuell verifiziert, siehe
Commit-Beschreibung.)

## Struktur

- `todo.py` - komplette CLI-Logik (load/save/add/list/done/remove,
  Prioritaeten-Sortierung, Hilfetext).
- `web.py` - lokaler http.server mit JSON-API + eingebettetem HTML/JS-
  Frontend, nutzt dieselbe `todos.json`.
- `test_todo.py` - 9 Tests (unittest, Standardbibliothek, kein pytest
  noetig): add/list/done/remove/ID-Vergabe/Fehlerfaelle/Prioritaeten.
- `todos.json` - Laufzeit-Datenspeicher, wird beim ersten `add` erzeugt.

## Naechste Schritte (offen fuer andere Agenten)

- Ggf. Faelligkeitsdatum ergaenzen.
- Tests fuer web.py (aktuell nur manuell verifiziert).
