"""Tests fuer todo.py. Ausfuehren mit: python3 -m unittest modules.cli-todo.test_todo
(oder direkt im Ordner: python3 -m unittest test_todo)"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import todo


class TodoTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._orig_store = todo.STORE
        todo.STORE = Path(self._tmpdir.name) / "todos.json"

    def tearDown(self):
        todo.STORE = self._orig_store
        self._tmpdir.cleanup()

    def test_add_and_list(self):
        todo.cmd_add(["Erste", "Aufgabe"])
        data = json.loads(todo.STORE.read_text())
        self.assertEqual(data, [{"id": 1, "text": "Erste Aufgabe", "done": False, "priority": "normal"}])

    def test_done(self):
        todo.cmd_add(["Aufgabe"])
        todo.cmd_done(["1"])
        data = json.loads(todo.STORE.read_text())
        self.assertTrue(data[0]["done"])

    def test_remove(self):
        todo.cmd_add(["Aufgabe"])
        todo.cmd_remove(["1"])
        data = json.loads(todo.STORE.read_text())
        self.assertEqual(data, [])

    def test_ids_increment_after_removal(self):
        todo.cmd_add(["A"])
        todo.cmd_add(["B"])
        todo.cmd_remove(["1"])
        todo.cmd_add(["C"])
        data = json.loads(todo.STORE.read_text())
        ids = sorted(t["id"] for t in data)
        self.assertEqual(ids, [2, 3])

    def test_done_unknown_id_fails(self):
        self.assertEqual(todo.cmd_done(["99"]), 1)

    def test_remove_unknown_id_fails(self):
        self.assertEqual(todo.cmd_remove(["99"]), 1)

    def test_add_with_priority(self):
        todo.cmd_add(["-p", "high", "Wichtig"])
        data = json.loads(todo.STORE.read_text())
        self.assertEqual(data[0]["priority"], "high")

    def test_add_with_invalid_priority_fails(self):
        self.assertEqual(todo.cmd_add(["-p", "urgent", "X"]), 1)

    def test_list_sorted_by_priority(self):
        todo.cmd_add(["-p", "low", "Niedrig"])
        todo.cmd_add(["-p", "high", "Hoch"])
        todo.cmd_add(["Normal"])
        data = json.loads(todo.STORE.read_text())
        order = [t["priority"] for t in todo.sorted_todos(data)]
        self.assertEqual(order, ["high", "normal", "low"])


if __name__ == "__main__":
    unittest.main()
