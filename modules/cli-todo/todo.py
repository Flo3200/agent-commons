#!/usr/bin/env python3
"""CLI-Todo-Tool - siehe modules/cli-todo/OVERVIEW.md fuer Details."""
import json
import sys
from pathlib import Path

STORE = Path(__file__).parent / "todos.json"


def load():
    if STORE.exists():
        return json.loads(STORE.read_text())
    return []


def save(todos):
    STORE.write_text(json.dumps(todos, indent=2, ensure_ascii=False))


def cmd_add(args):
    if not args:
        print("Fehler: Text fuer 'add' fehlt.")
        return 1
    todos = load()
    todos.append({"id": (todos[-1]["id"] + 1 if todos else 1), "text": " ".join(args), "done": False})
    save(todos)
    print(f"Hinzugefuegt: #{todos[-1]['id']} {todos[-1]['text']}")
    return 0


def cmd_list(args):
    todos = load()
    if not todos:
        print("Keine Todos.")
        return 0
    for t in todos:
        mark = "x" if t["done"] else " "
        print(f"[{mark}] #{t['id']} {t['text']}")
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
    if not argv or argv[0] not in COMMANDS:
        print("Nutzung: todo.py <add|list|done|remove> [args]")
        return 1
    return COMMANDS[argv[0]](argv[1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
