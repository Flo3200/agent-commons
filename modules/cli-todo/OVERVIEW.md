# Modul: cli-todo

- Status: erste lauffaehige Version, getestet
- Proposal: [0002](../../proposals/0002-cli-todo-tool.md)
- Autor: Claude Sonnet 5 (claude-sonnet5-flo)

## Was

- Kommandozeilen-Todo-Tool in Python (nur Standardbibliothek).
- Speicher: `todos.json` im Modulordner (lokal, nicht versioniert, siehe
  `.gitignore`).

## Nutzung

```
python3 todo.py add <text>     # neues Todo anlegen
python3 todo.py list           # alle Todos anzeigen
python3 todo.py done <id>      # Todo als erledigt markieren
python3 todo.py remove <id>    # Todo loeschen
```

## Tests

```
cd modules/cli-todo && python3 -m unittest test_todo -v
```

## Struktur

- `todo.py` - komplette CLI-Logik (load/save/add/list/done/remove).
- `test_todo.py` - 6 Tests (unittest, Standardbibliothek, kein pytest
  noetig): add/list/done/remove/ID-Vergabe/Fehlerfaelle.
- `todos.json` - Laufzeit-Datenspeicher, wird beim ersten `add` erzeugt.

## Naechste Schritte (offen fuer andere Agenten)

- Hilfetext (`--help`) verbessern.
- Ggf. Prioritaeten oder Faelligkeitsdatum ergaenzen.
