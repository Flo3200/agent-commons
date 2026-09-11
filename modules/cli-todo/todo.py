#!/usr/bin/env python3
"""CLI-Todo-Tool - siehe modules/cli-todo/OVERVIEW.md fuer Details."""
import json
import sys
from pathlib import Path

STORE = Path(__file__).parent / "todos.json"
PRIORITIES = ("low", "normal", "high")
PRIORITY_ORDER = {"high": 0, "normal": 1, "low": 2}

HELP = """Nutzung: todo.py <add|list|done|remove> [args]

Befehle:
  add <text> [-p low|normal|high]   Neues Todo anlegen (Standard: normal)
  list                               Alle Todos anzeigen (nach Prioritaet sortiert)
  done <id>                          Todo als erledigt markieren
  remove <id>                        Todo loeschen

Beispiele:
  python3 todo.py add "Einkaufen" -p high
  python3 todo.py list
  python3 todo.py done 1
  python3 todo.py remove 2
"""


def load():
    if STORE.exists():
        todos = json.loads(STORE.read_text())
        for t in todos:
            t.setdefault("priority", "normal")  # Migration alter Eintraege
        return todos
    return []


def save(todos):
    STORE.write_text(json.dumps(todos, indent=2, ensure_ascii=False))


def sorted_todos(todos):
    return sorted(todos, key=lambda t: (t["done"], PRIORITY_ORDER.get(t.get("priority", "normal"), 1)))


def cmd_add(args):
    priority = "normal"
    if "-p" in args:
        idx = args.index("-p")
        if idx + 1 >= len(args) or args[idx + 1] not in PRIORITIES:
            print(f"Fehler: -p braucht einen Wert aus {PRIORITIES}.")
            return 1
        priority = args[idx + 1]
        args = args[:idx] + args[idx + 2:]
    if not args:
        print("Fehler: Text fuer 'add' fehlt.")
        return 1
    todos = load()
    todos.append({
        "id": (todos[-1]["id"] + 1 if todos else 1),
        "text": " ".join(args),
        "done": False,
        "priority": priority,
    })
    save(todos)
    print(f"Hinzugefuegt: #{todos[-1]['id']} ({priority}) {todos[-1]['text']}")
    return 0


def cmd_list(args):
    todos = load()
    if not todos:
        print("Keine Todos.")
        return 0
    for t in sorted_todos(todos):
        mark = "x" if t["done"] else " "
        print(f"[{mark}] #{t['id']} ({t.get('priority', 'normal')}) {t['text']}")
    return 0


def cmd_done(args):
    if not args or not args[0].isdigit():
        print("Fehler: 'done' braucht eine gueltige ID.")
        return 1
    todos = load()
    for t in todos:
        if t["id"] == int(args[0]):
            t["done"] = True
            save(todos)
            print(f"Erledigt: #{t['id']} {t['text']}")
            return 0
    print(f"Keine Todo mit ID {args[0]} gefunden.")
    return 1


def cmd_remove(args):
    if not args or not args[0].isdigit():
        print("Fehler: 'remove' braucht eine gueltige ID.")
        return 1
    todos = load()
    new_todos = [t for t in todos if t["id"] != int(args[0])]
    if len(new_todos) == len(todos):
        print(f"Keine Todo mit ID {args[0]} gefunden.")
        return 1
    save(new_todos)
    print(f"Entfernt: #{args[0]}")
    return 0


COMMANDS = {"add": cmd_add, "list": cmd_list, "done": cmd_done, "remove": cmd_remove}


def main(argv):
    if not argv or argv[0] in ("--help", "-h") or argv[0] not in COMMANDS:
        print(HELP)
        return 0 if argv and argv[0] in ("--help", "-h") else 1
    return COMMANDS[argv[0]](argv[1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
