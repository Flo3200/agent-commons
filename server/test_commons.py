"""Tests fuer commons.py. Ausfuehren mit: python3 -m unittest test_commons -v"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import commons


class CommonsStateTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._orig_state_file = commons.STATE_FILE
        commons.STATE_FILE = str(Path(self._tmpdir.name) / "commons_state.json")
        self.state = commons.CommonsState()

    def tearDown(self):
        commons.STATE_FILE = self._orig_state_file
        self._tmpdir.cleanup()

    def test_checkin_updates_roster_and_activity(self):
        self.state.checkin("sonnet-a", "liest README", "")
        agents = self.state.agents_public()
        self.assertIn("sonnet-a", agents)
        self.assertEqual(agents["sonnet-a"]["status"], "liest README")
        activity = self.state.activity_public()
        self.assertEqual(len(activity), 1)
        self.assertEqual(activity[0]["agent_id"], "sonnet-a")

    def test_checkin_overwrites_previous_roster_entry(self):
        self.state.checkin("sonnet-a", "liest README", "")
        self.state.checkin("sonnet-a", "baut Modul", "Schritt 1")
        agents = self.state.agents_public()
        self.assertEqual(agents["sonnet-a"]["status"], "baut Modul")
        # Verlauf behaelt aber beide Eintraege
        self.assertEqual(len(self.state.activity_public()), 2)

    def test_send_message_broadcast_and_directed(self):
        self.state.send_message("sonnet-a", "", "an alle")
        self.state.send_message("sonnet-a", "haiku-1", "nur fuer dich")
        msgs = self.state.messages_public()
        self.assertEqual(len(msgs), 2)
        self.assertIsNone(msgs[0]["to"])
        self.assertEqual(msgs[1]["to"], "haiku-1")

    def test_messages_since_id_filters_older(self):
        self.state.send_message("a", "", "eins")
        self.state.send_message("a", "", "zwei")
        self.state.send_message("a", "", "drei")
        recent = self.state.messages_public(since_id=1)
        self.assertEqual([m["text"] for m in recent], ["zwei", "drei"])

    def test_delete_message(self):
        self.state.send_message("a", "", "eins")
        msg_id = self.state.messages_public()[0]["id"]
        ok = self.state.delete_message(msg_id)
        self.assertTrue(ok)
        self.assertEqual(self.state.messages_public(), [])
        self.assertFalse(self.state.delete_message(msg_id))

    def test_proposals_add_list_delete(self):
        self.state.add_proposal("Flo", "Lasst uns X bauen")
        props = self.state.proposals_public()
        self.assertEqual(len(props), 1)
        self.assertEqual(props[0]["author"], "Flo")
        self.assertTrue(self.state.delete_proposal(props[0]["id"]))
        self.assertEqual(self.state.proposals_public(), [])

    def test_state_persists_across_reload(self):
        self.state.checkin("sonnet-a", "liest README", "")
        self.state.send_message("sonnet-a", "", "hallo")
        self.state.add_proposal("Flo", "Idee")
        reloaded = commons.CommonsState()
        self.assertIn("sonnet-a", reloaded.agents_public())
        self.assertEqual(len(reloaded.messages_public()), 1)
        self.assertEqual(len(reloaded.proposals_public()), 1)
        with open(commons.STATE_FILE, encoding="utf-8") as f:
            on_disk = json.load(f)
        self.assertIn("agents", on_disk)

    def test_ids_increment_independently_per_collection(self):
        self.state.send_message("a", "", "m1")
        self.state.add_proposal("a", "p1")
        msg_id = self.state.messages_public()[0]["id"]
        prop_id = self.state.proposals_public()[0]["id"]
        self.assertEqual(msg_id, 1)
        self.assertEqual(prop_id, 1)


if __name__ == "__main__":
    unittest.main()
