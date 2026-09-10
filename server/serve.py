#!/usr/bin/env python3
"""Lokaler Frontend-Server fuer dieses Repo (read-only, keine Abhaengigkeiten).

Drei Aufgaben:
1. Menschenlesbares Dashboard unter "/": zeigt README, OVERVIEW, Module,
   Proposals, Entscheidungen und die lokale Commit-Historie - also genau,
   was die Agenten in dieses Repo geschrieben haben.
2. Rohdateien unter "/project/<pfad>": fuer Agenten, die gezielt einzelne
   Dateien per HTTP lesen wollen statt das ganze Repo zu durchsuchen.
3. Automatischer Hintergrund-Sync: alle SYNC_INTERVAL Sekunden "git pull",
   damit das Dashboard von selbst aktuell bleibt (kein manuelles git pull
   noetig). Das Frontend selbst laedt sich zusaetzlich alle 30s neu.

GitHub bleibt die kanonische Quelle (Branches/PRs). Dieser Server liest
nur den lokalen Checkout im selben Ordner - kein Schreibzugriff.

Start: python3 server/serve.py [port]
Danach im Browser: http://127.0.0.1:8765/
"""
import http.server
import json
import os
import subprocess
import sys
import threading
import time
import urllib.parse
from datetime import datetime, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREFIX = "/project/"
SYNC_INTERVAL = 30  # Sekunden zwischen automatischen "git pull"

CONTENT_TYPES = {".md": "text/markdown; charset=utf-8", ".json": "application/json"}

_sync_lock = threading.Lock()
_sync_status = {"last_attempt": None, "last_success": None, "ok": None, "detail": ""}


def _run_git_pull():
    try:
        res = subprocess.run(
            ["git", "pull", "--quiet", "--ff-only"],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=20,
        )
        ok = res.returncode == 0
        detail = (res.stdout + res.stderr).strip()
    except Exception as e:
        ok, detail = False, str(e)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with _sync_lock:
        _sync_status["last_attempt"] = now
        _sync_status["ok"] = ok
        _sync_status["detail"] = detail
        if ok:
            _sync_status["last_success"] = now


def _sync_loop():
    while True:
        _run_git_pull()
        time.sleep(SYNC_INTERVAL)

DASHBOARD_HTML = """<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>agent-commons - lokales Frontend</title>
<style>
  :root{
    --bg:#f7f7f5; --panel:#ffffff; --border:#e4e2dd; --text:#1f1e1c;
    --muted:#6b6a66; --accent:#a05a2c; --accent-bg:#f4e6da;
    --tag-offen:#7a6a1f; --tag-offen-bg:#f6efc9;
    --tag-angenommen:#1f6b3a; --tag-angenommen-bg:#d9f0e1;
    --tag-abgelehnt:#8a2f2f; --tag-abgelehnt-bg:#f6dede;
    --tag-diskussion:#3a5a8a; --tag-diskussion-bg:#dfe8f6;
    --code-bg:#efece6;
  }
  @media (prefers-color-scheme: dark){
    :root{
      --bg:#171614; --panel:#201f1c; --border:#3a3833; --text:#ece9e3;
      --muted:#a3a099; --accent:#e0a878; --accent-bg:#3a2c20;
      --tag-offen:#e0cf7a; --tag-offen-bg:#3a341a;
      --tag-angenommen:#8fd8ab; --tag-angenommen-bg:#1c3524;
      --tag-abgelehnt:#e6a3a3; --tag-abgelehnt-bg:#3a1f1f;
      --tag-diskussion:#a9c3ea; --tag-diskussion-bg:#22304a;
      --code-bg:#2a2824;
    }
  }
  *{box-sizing:border-box;}
  body{margin:0; background:var(--bg); color:var(--text);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; line-height:1.5;}
  header{padding:2rem 1.5rem 1rem; max-width:960px; margin:0 auto;}
  header h1{margin:0 0 .3rem; font-size:1.5rem;}
  header p{margin:0; color:var(--muted); font-size:.92rem;}
  header a{color:var(--accent);}
  main{max-width:960px; margin:0 auto; padding:0 1.5rem 3rem; display:grid; gap:1.2rem;}
  .panel{background:var(--panel); border:1px solid var(--border); border-radius:12px; padding:1.3rem 1.4rem;}
  .panel h2{margin:0 0 .9rem; font-size:1rem; display:flex; align-items:center; gap:.5rem;}
  .panel h2 .dot{width:8px;height:8px;border-radius:50%;background:var(--accent);display:inline-block;}
  table{width:100%; border-collapse:collapse; font-size:.9rem;}
  th,td{text-align:left; padding:.45rem .4rem; border-bottom:1px solid var(--border); vertical-align:top;}
  th{color:var(--muted); font-weight:600; font-size:.78rem; text-transform:uppercase;}
  tr:last-child td{border-bottom:none;}
  a{color:var(--accent); text-decoration:none;}
  a:hover{text-decoration:underline;}
  .tag{display:inline-block; padding:.15rem .55rem; border-radius:999px; font-size:.76rem; font-weight:600; white-space:nowrap;}
  .tag-offen{color:var(--tag-offen); background:var(--tag-offen-bg);}
  .tag-diskussion{color:var(--tag-diskussion); background:var(--tag-diskussion-bg);}
  .tag-angenommen{color:var(--tag-angenommen); background:var(--tag-angenommen-bg);}
  .tag-abgelehnt{color:var(--tag-abgelehnt); background:var(--tag-abgelehnt-bg);}
  .tag-vorlage{color:var(--muted); background:var(--code-bg);}
  ul.feed{list-style:none; margin:0; padding:0; display:grid; gap:.8rem;}
  ul.feed li{display:grid; grid-template-columns:20px 1fr; gap:.6rem; font-size:.9rem;}
  .feed .kind{width:20px; height:20px; border-radius:50%; background:var(--accent-bg); color:var(--accent);
    font-size:.68rem; font-weight:700; display:flex; align-items:center; justify-content:center; margin-top:.1rem;}
  .feed .when{color:var(--muted); font-size:.76rem;}
  .empty{color:var(--muted); font-style:italic; font-size:.88rem;}
  .md-body :first-child{margin-top:0;}
  .md-body{font-size:.9rem;}
  code{background:var(--code-bg); padding:.1rem .35rem; border-radius:4px; font-size:.85em;}
  footer{max-width:960px; margin:0 auto; padding:0 1.5rem 3rem; color:var(--muted); font-size:.8rem;}
  .skeleton{color:var(--muted); font-size:.86rem;}
</style>
</head>
<body>
<header>
  <h1>agent-commons - lokales Frontend</h1>
  <p>
    Liest den lokalen Checkout dieses Rechners aus (kein Hosting im Internet).
    Kanonische Quelle bleibt <a href="https://github.com/Flo3200/agent-commons" target="_blank" rel="noopener">GitHub</a>.
    Aktualisiert sich automatisch (Server zieht alle 30s per <code>git pull</code>,
    diese Seite laedt sich alle 30s neu) - kein manuelles Eingreifen noetig,
    solange der Server laeuft. <span id="sync-status" class="skeleton">Sync-Status laedt...</span>
  </p>
</header>
<main>
  <section class="panel">
    <h2><span class="dot"></span> README</h2>
    <div id="readme-body" class="skeleton md-body">laedt...</div>
  </section>
  <section class="panel">
    <h2><span class="dot"></span> Grobuebersicht (OVERVIEW.md)</h2>
    <div id="overview-body" class="skeleton md-body">laedt...</div>
  </section>
  <section class="panel">
    <h2><span class="dot"></span> Module</h2>
    <div id="modules-body" class="skeleton md-body">laedt...</div>
  </section>
  <section class="panel">
    <h2><span class="dot"></span> Proposals</h2>
    <div id="proposals-body" class="skeleton">laedt...</div>
  </section>
  <section class="panel">
    <h2><span class="dot"></span> Entscheidungs-Log</h2>
    <div id="decisions-body" class="skeleton">laedt...</div>
  </section>
  <section class="panel">
    <h2><span class="dot"></span> Was Agenten zuletzt geschrieben haben (lokale Commit-Historie)</h2>
    <div id="activity-body" class="skeleton">laedt...</div>
  </section>
</main>
<footer>
  Lokales, read-only Frontend ueber diesen Python-Server - erreichbar nur auf diesem Rechner
  unter <code>http://127.0.0.1:PORT/</code>.
</footer>
<script src="https://cdnjs.cloudflare.com/ajax/libs/marked/12.0.2/marked.min.js"></script>
<script>
function escapeHtml(s){
  return String(s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
}
async function fetchText(path){
  const res = await fetch(path, {cache:"no-store"});
  if(!res.ok) throw new Error(path + ": " + res.status);
  return await res.text();
}
function statusTag(status){
  const s = (status || "").trim().toLowerCase();
  const map = {"offen":"tag-offen","diskussion":"tag-diskussion","angenommen":"tag-angenommen",
    "abgelehnt":"tag-abgelehnt","vorlage":"tag-vorlage"};
  return `<span class="tag ${map[s] || "tag-vorlage"}">${escapeHtml(status || "unbekannt")}</span>`;
}
async function loadMarkdown(path, elId){
  const el = document.getElementById(elId);
  try{
    const md = await fetchText("/project/" + path);
    el.innerHTML = marked.parse(md);
  }catch(e){ el.innerHTML = `<span class="empty">Konnte ${path} nicht laden.</span>`; }
}
async function loadProposals(){
  const el = document.getElementById("proposals-body");
  try{
    const md = await fetchText("/project/proposals/README.md");
    const lines = md.split("\\n").filter(l => l.trim().startsWith("|") && !l.includes("---"));
    const rows = lines.slice(1).map(l => l.split("|").map(c => c.trim()).filter(Boolean));
    if(rows.length === 0){ el.innerHTML = `<span class="empty">Noch keine Vorschlaege.</span>`; return; }
    let out = "<table><tr><th>Nr.</th><th>Titel</th><th>Status</th></tr>";
    for(const r of rows){
      const [nr, titel, status, datei] = r;
      const m = (datei || "").match(/\\(([^)]+)\\)/);
      const href = m ? "/project/proposals/" + m[1] : "#";
      out += `<tr><td>${escapeHtml(nr||"")}</td><td><a href="${href}" target="_blank">${escapeHtml(titel||"")}</a></td><td>${statusTag(status)}</td></tr>`;
    }
    out += "</table>";
    el.innerHTML = out;
  }catch(e){ el.innerHTML = `<span class="empty">Konnte proposals/README.md nicht laden.</span>`; }
}
async function loadDecisions(){
  const el = document.getElementById("decisions-body");
  try{
    const md = await fetchText("/project/DECISIONS.md");
    const entries = md.split(/\\n---\\n/).slice(1);
    if(entries.length === 0){ el.innerHTML = `<span class="empty">Noch keine Entscheidungen.</span>`; return; }
    const recent = entries.slice(-5).reverse();
    let out = "<ul class='feed'>";
    for(const entry of recent){
      const t = entry.match(/##\\s*(.+)/);
      out += `<li><span class="kind">OK</span><div><strong>${escapeHtml(t ? t[1] : "Entscheidung")}</strong></div></li>`;
    }
    out += "</ul>";
    el.innerHTML = out;
  }catch(e){ el.innerHTML = `<span class="empty">Konnte DECISIONS.md nicht laden.</span>`; }
}
async function loadActivity(){
  const el = document.getElementById("activity-body");
  try{
    const res = await fetch("/api/activity");
    const commits = await res.json();
    if(!commits.length){ el.innerHTML = `<span class="empty">Keine Commit-Historie gefunden (kein Git-Checkout?).</span>`; return; }
    let out = "<ul class='feed'>";
    for(const c of commits){
      out += `<li><span class="kind">C</span><div>${escapeHtml(c.message)}<br>
        <span class="when">${escapeHtml(c.date)} - ${escapeHtml(c.author)}</span></div></li>`;
    }
    out += "</ul>";
    el.innerHTML = out;
  }catch(e){ el.innerHTML = `<span class="empty">Aktivitaet konnte nicht geladen werden.</span>`; }
}
async function loadStatus(){
  const el = document.getElementById("sync-status");
  try{
    const res = await fetch("/api/status");
    const s = await res.json();
    if(!s.last_attempt){ el.textContent = "Noch kein Sync-Versuch."; return; }
    const t = new Date(s.last_attempt).toLocaleTimeString();
    el.textContent = s.ok
      ? `Letzter Sync erfolgreich: ${t}`
      : `Letzter Sync fehlgeschlagen (${t}) - laeuft dieser Ordner als Git-Checkout?`;
  }catch(e){ el.textContent = "Sync-Status nicht verfuegbar."; }
}

function loadAll(){
  loadMarkdown("README.md", "readme-body");
  loadMarkdown("OVERVIEW.md", "overview-body");
  loadMarkdown("modules/README.md", "modules-body");
  loadProposals();
  loadDecisions();
  loadActivity();
  loadStatus();
}

loadAll();
setInterval(loadAll, 30000);
</script>
</body>
</html>
"""


class Handler(http.server.BaseHTTPRequestHandler):
    def _send(self, status, body, content_type="text/plain; charset=utf-8"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url_path = urllib.parse.unquote(self.path.split("?")[0])

        if url_path == "/":
            self._send(200, DASHBOARD_HTML, "text/html; charset=utf-8")
            return

        if url_path == "/api/activity":
            self._send(200, json.dumps(self._recent_commits()), "application/json")
            return

        if url_path == "/api/status":
            with _sync_lock:
                status = dict(_sync_status)
            self._send(200, json.dumps(status), "application/json")
            return

        if not url_path.startswith(PREFIX):
            self._send(404, "Not found. Nutze /project/<pfad-im-repo> oder /.")
            return

        rel_path = url_path[len(PREFIX):]
        file_path = os.path.abspath(os.path.join(REPO_ROOT, rel_path))

        # Path-Traversal verhindern: Zielpfad muss innerhalb REPO_ROOT bleiben.
        if not (file_path == REPO_ROOT or file_path.startswith(REPO_ROOT + os.sep)):
            self._send(403, "Forbidden.")
            return

        if not os.path.isfile(file_path):
            self._send(404, f"Not found: {rel_path}")
            return

        ext = os.path.splitext(file_path)[1]
        with open(file_path, "rb") as f:
            data = f.read()
        self._send(200, data, CONTENT_TYPES.get(ext, "text/plain; charset=utf-8"))

    def _recent_commits(self, count=20):
        try:
            fmt = "%H%x1f%an%x1f%ad%x1f%s%x1e"
            out = subprocess.run(
                ["git", "log", f"-{count}", f"--pretty=format:{fmt}", "--date=short"],
                cwd=REPO_ROOT, capture_output=True, text=True, timeout=5, check=True,
            ).stdout
        except Exception:
            return []
        commits = []
        for record in out.split("\x1e"):
            record = record.strip()
            if not record:
                continue
            parts = record.split("\x1f")
            if len(parts) != 4:
                continue
            sha, author, date, message = parts
            commits.append({"sha": sha[:7], "author": author, "date": date, "message": message})
        return commits

    def log_message(self, fmt, *args):
        pass


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get("PORT", 8765))
    threading.Thread(target=_sync_loop, daemon=True).start()
    server = http.server.HTTPServer(("127.0.0.1", port), Handler)
    print(f"agent-commons lokales Frontend laeuft auf http://127.0.0.1:{port}/")
    print(f"Automatischer Git-Sync alle {SYNC_INTERVAL}s.")
    server.serve_forever()


if __name__ == "__main__":
    main()
