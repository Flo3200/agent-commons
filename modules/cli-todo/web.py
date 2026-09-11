#!/usr/bin/env python3
"""Lokales Web-Frontend fuer das cli-todo-Modul (Python-Standardlib).

Nutzt dieselbe todos.json und dieselbe Lade-/Speicherlogik wie todo.py -
CLI und Web-UI koennen parallel benutzt werden. Bindet nur an 127.0.0.1.

Start: python3 web.py [port]  (Standard: 8766)
Danach im Browser: http://127.0.0.1:8766/
"""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import todo  # noqa: E402

PAGE = """<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>cli-todo - Web</title>
<style>
  :root{ --bg:#f7f7f5; --panel:#fff; --border:#e4e2dd; --text:#1f1e1c; --muted:#6b6a66; --accent:#a05a2c; }
  @media (prefers-color-scheme: dark){
    :root{ --bg:#171614; --panel:#201f1c; --border:#3a3833; --text:#ece9e3; --muted:#a3a099; --accent:#e0a878; }
  }
  body{margin:0; background:var(--bg); color:var(--text); font-family:-apple-system,sans-serif; padding:2rem;}
  main{max-width:560px; margin:0 auto;}
  h1{font-size:1.3rem;}
  form{display:flex; gap:.5rem; margin-bottom:1rem;}
  input[type=text]{flex:1; padding:.5rem; border:1px solid var(--border); border-radius:6px; background:var(--panel); color:var(--text);}
  select, button{padding:.5rem; border-radius:6px; border:1px solid var(--border); background:var(--panel); color:var(--text); cursor:pointer;}
  ul{list-style:none; padding:0;}
  li{display:flex; gap:.6rem; align-items:baseline; padding:.5rem 0; border-bottom:1px solid var(--border);}
  li.done .text{text-decoration:line-through; color:var(--muted);}
  .prio{font-size:.75rem; padding:.1rem .4rem; border-radius:999px; background:var(--border);}
  .text{flex:1;}
  .del{background:none; border:none; color:var(--muted); cursor:pointer;}
</style>
</head>
<body>
<main>
  <h1>cli-todo</h1>
  <form id="f">
    <input type="text" id="text" placeholder="Neues Todo" required>
    <select id="prio"><option value="normal" selected>normal</option><option value="high">high</option><option value="low">low</option></select>
    <button type="submit">+</button>
  </form>
  <ul id="list"></ul>
</main>
<script>
async function load(){
  const res = await fetch("/api/todos");
  const todos = await res.json();
  const el = document.getElementById("list");
  el.innerHTML = "";
  for(const t of todos){
    const li = document.createElement("li");
    if(t.done) li.className = "done";
    li.innerHTML = `<input type="checkbox" ${t.done?"checked":""}> <span class="prio">${t.priority}</span> <span class="text"></span> <button class="del">✕</button>`;
    li.querySelector(".text").textContent = t.text;
    li.querySelector("input").addEventListener("change", async () => {
      await fetch(`/api/todos/${t.id}/done`, {method:"POST"});
      load();
    });
    li.querySelector(".del").addEventListener("click", async () => {
      await fetch(`/api/todos/${t.id}`, {method:"DELETE"});
      load();
    });
    el.appendChild(li);
  }
}
document.getElementById("f").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const text = document.getElementById("text").value.trim();
  const priority = document.getElementById("prio").value;
  if(!text) return;
  await fetch("/api/todos", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({text, priority})});
  document.getElementById("text").value = "";
  load();
});
load();
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, body):
        body = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_GET(self):
        if self.path == "/":
            self._send_html(PAGE)
            return
        if self.path == "/api/todos":
            self._send_json(todo.sorted_todos(todo.load()))
            return
        self._send_json({"error": "not found"}, 404)

    def do_POST(self):
        if self.path == "/api/todos":
            body = self._read_json()
            text = str(body.get("text", "")).strip()
            priority = body.get("priority", "normal")
            if not text or priority not in todo.PRIORITIES:
                self._send_json({"error": "text und gueltige priority erforderlich"}, 400)
                return
            todos = todo.load()
            new_todo = {"id": (todos[-1]["id"] + 1 if todos else 1), "text": text, "done": False, "priority": priority}
            todos.append(new_todo)
            todo.save(todos)
            self._send_json(new_todo)
            return
        if self.path.startswith("/api/todos/") and self.path.endswith("/done"):
            todo_id = int(self.path.split("/")[3])
            todos = todo.load()
            for t in todos:
                if t["id"] == todo_id:
                    t["done"] = True
                    todo.save(todos)
                    self._send_json(t)
                    return
            self._send_json({"error": "not found"}, 404)
            return
        self._send_json({"error": "not found"}, 404)

    def do_DELETE(self):
        if self.path.startswith("/api/todos/"):
            todo_id = int(self.path.split("/")[3])
            todos = todo.load()
            new_todos = [t for t in todos if t["id"] != todo_id]
            if len(new_todos) == len(todos):
                self._send_json({"error": "not found"}, 404)
                return
            todo.save(new_todos)
            self._send_json({"ok": True})
            return
        self._send_json({"error": "not found"}, 404)

    def log_message(self, fmt, *args):
        pass


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8766
    server = HTTPServer(("127.0.0.1", port), Handler)
    print(f"cli-todo Web-Frontend laeuft auf http://127.0.0.1:{port}/")
    server.serve_forever()


if __name__ == "__main__":
    main()
