"""State fuer die agent-commons Live-Ansicht: Roster, Chat, Taetigkeits-Log.

Gleiches Muster wie die State-Klassen der anderen lokalen Module hier
(z.B. game.py/forum.py aus ai-society-concept): EINE Klasse haelt den
kompletten Zustand als Dict im Speicher und schreibt ihn nach JEDER
Aenderung atomar als JSON auf Platte (server/data/commons_state.json).

Dadurch ist alles schon jetzt dauerhaft gespeichert - Server-Neustart
oder Rechner-Runterfahren ist egal, die Datei liegt einfach da und wird
beim naechsten Start wieder eingelesen. Kein Datenbank-Server, keine
Abhaengigkeiten - nur json + Standardlib.
"""
import json
import os
import threading
from datetime import datetime, timezone

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
STATE_FILE = os.path.join(DATA_DIR, "commons_state.json")

MESSAGES_KEEP = 200   # Chat-Verlauf: nur die letzten N behalten
ACTIVITY_KEEP = 200   # Taetigkeits-Log: nur die letzten N behalten
PROPOSALS_KEEP = 100  # Vorschlaege-Pinnwand: nur die letzten N behalten
AGENT_FRESH_WITHIN = 5 * 60  # Sekunden, danach zeigt der Punkt "nicht mehr frisch"


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class CommonsState:
    """Ein Objekt, ein Lock, eine Datei - wie GameState/ForumState."""

    def __init__(self):
        self._lock = threading.Lock()
        self.state = self._load()

    def _load(self):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
        data.setdefault("agents", {})
        data.setdefault("messages", [])
        data.setdefault("activity", [])
        data.setdefault("proposals", [])
        return data

    def _save(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        tmp_path = STATE_FILE + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, STATE_FILE)  # atomar: nie eine halb geschriebene Datei

    def _next_id(self, key):
        items = self.state[key]
        return (items[-1]["id"] + 1) if items else 1

    # ---------- Roster + Taetigkeits-Log: ein Check-in aktualisiert beides ----------

    def checkin(self, agent_id, status, detail):
        with self._lock:
            now = _now()
            self.state["agents"][agent_id] = {"status": status, "detail": detail, "at": now}
            self.state["activity"].append({
                "id": self._next_id("activity"),
                "agent_id": agent_id,
                "status": status,
                "detail": detail,
                "at": now,
            })
            self.state["activity"] = self.state["activity"][-ACTIVITY_KEEP:]
            self._save()

    def agents_public(self):
        """Roster: wer ist da, mit letztem Status + Frische-Indikator."""
        with self._lock:
            agents = dict(self.state["agents"])
        now = datetime.now(timezone.utc)
        out = {}
        for agent_id, entry in agents.items():
            try:
                age = (now - datetime.fromisoformat(entry["at"])).total_seconds()
            except Exception:
                age = 0
            out[agent_id] = {**entry, "fresh": age <= AGENT_FRESH_WITHIN}
        return out

    def activity_public(self, limit=50):
        with self._lock:
            entries = list(self.state["activity"][-limit:])
        now = datetime.now(timezone.utc)
        out = []
        for entry in entries:
            try:
                age = (now - datetime.fromisoformat(entry["at"])).total_seconds()
            except Exception:
                age = 0
            out.append({**entry, "fresh": age <= AGENT_FRESH_WITHIN})
        return out

    # ---------- Chat zwischen Agenten ----------

    def send_message(self, from_id, to_id, text):
        with self._lock:
            self.state["messages"].append({
                "id": self._next_id("messages"),
                "from": from_id,
                "to": to_id or None,  # leer/None = oeffentlich an alle
                "text": text,
                "at": _now(),
            })
            self.state["messages"] = self.state["messages"][-MESSAGES_KEEP:]
            self._save()

    def messages_public(self, limit=50, since_id=None, to=None):
        """to=<agent_id> filtert auf Broadcasts + an diesen Agenten gerichtete
        Nachrichten - damit ein wartender Agent nur seinen eigenen Ausschnitt
        abfragen kann, statt den ganzen Chat zu lesen (spart Tokens)."""
        with self._lock:
            msgs = list(self.state["messages"])
        if since_id is not None:
            msgs = [m for m in msgs if m["id"] > since_id]
        if to:
            msgs = [m for m in msgs if m["to"] is None or m["to"] == to]
        return msgs[-limit:]

    def delete_message(self, msg_id):
        with self._lock:
            before = len(self.state["messages"])
            self.state["messages"] = [m for m in self.state["messages"] if m["id"] != msg_id]
            changed = len(self.state["messages"]) != before
            if changed:
                self._save()
            return changed

    # ---------- Vorschlaege-Pinnwand (an alle, Agenten UND Mensch) ----------

    def add_proposal(self, author, text):
        with self._lock:
            self.state["proposals"].append({
                "id": self._next_id("proposals"),
                "author": author,
                "text": text,
                "at": _now(),
            })
            self.state["proposals"] = self.state["proposals"][-PROPOSALS_KEEP:]
            self._save()

    def proposals_public(self, limit=50):
        with self._lock:
            return list(self.state["proposals"][-limit:])

    def delete_proposal(self, proposal_id):
        with self._lock:
            before = len(self.state["proposals"])
            self.state["proposals"] = [p for p in self.state["proposals"] if p["id"] != proposal_id]
            changed = len(self.state["proposals"]) != before
            if changed:
                self._save()
            return changed
