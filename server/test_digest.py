"""Tests fuer digest.py. Ausfuehren mit: python3 -m unittest test_digest -v"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import commons
from digest import build_digest


class DigestTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._orig_state_file = commons.STATE_FILE
        commons.STATE_FILE = str(Path(self._tmpdir.name) / "commons_state.json")
        self.state = commons.CommonsState()

    def tearDown(self):
        commons.STATE_FILE = self._orig_state_file
        self._tmpdir.cleanup()

    def _today(self):
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def test_empty_state_still_produces_valid_digest(self):
        text = build_digest(self.state)
        self.assertIn(self._today(), text)
        self.assertIn("0 Agent(en) aktiv", text)

    def test_counts_agents_checkins_and_proposals(self):
        self.state.checkin("sonnet-a", "baut X", "Schritt 1")
        self.state.checkin("haiku-1", "liest README", "")
        self.state.checkin("sonnet-a", "baut X", "Schritt 2")  # gleicher Agent, 2. Checkin
        self.state.add_proposal("Flo", "Idee A")
        text = build_digest(self.state)
        self.assertIn("2 Agent(en) aktiv: haiku-1, sonnet-a", text)
        self.assertIn("3 Check-ins insgesamt", text)
        self.assertIn("1 neue Vorschlaege", text)
        self.assertIn("Idee A", text)

    def test_shows_latest_status_per_agent_not_all(self):
        self.state.checkin("sonnet-a", "Schritt 1", "")
        self.state.checkin("sonnet-a", "Schritt 2 (aktuell)", "")
        text = build_digest(self.state)
        self.assertIn("Schritt 2 (aktuell)", text)
        # Nur der letzte Status wird in der Zusammenfassung gezeigt, nicht Schritt 1
        self.assertNotIn("**sonnet-a**: Schritt 1", text)

    def test_shows_active_claims(self):
        self.state.claim("sonnet-a", "modules/cli-todo", "baue Prioritaeten")
        text = build_digest(self.state)
        self.assertIn("1 aktive Claims", text)
        self.assertIn("modules/cli-todo", text)
        self.assertIn("sonnet-a", text)

    def test_day_filter_excludes_other_days(self):
        self.state.checkin("sonnet-a", "heute", "")
        text = build_digest(self.state, day="2000-01-01")
        self.assertIn("0 Agent(en) aktiv", text)
        self.assertIn("2000-01-01", text)


if __name__ == "__main__":
    unittest.main()
