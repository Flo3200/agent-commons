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

    def test_claim_and_list(self):
        claim = self.state.claim("sonnet-a", "modules/cli-todo", "baue CLI")
        self.assertEqual(claim["agent_id"], "sonnet-a")
        claims = self.state.claims_public()
        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0]["name"], "modules/cli-todo")

    def test_claim_blocks_other_agent(self):
        self.state.claim("sonnet-a", "modules/cli-todo", "baue CLI")
        blocked = self.state.claim("haiku-1", "modules/cli-todo", "baue auch CLI")
        self.assertIsNone(blocked)
        self.assertEqual(len(self.state.claims_public()), 1)

    def test_same_agent_can_renew_own_claim(self):
        self.state.claim("sonnet-a", "modules/cli-todo", "Schritt 1")
        renewed = self.state.claim("sonnet-a", "modules/cli-todo", "Schritt 2")
        self.assertIsNotNone(renewed)
        self.assertEqual(renewed["note"], "Schritt 2")
        self.assertEqual(len(self.state.claims_public()), 1)

    def test_release_claim_only_by_owner(self):
        self.state.claim("sonnet-a", "modules/cli-todo", "baue CLI")
        self.assertFalse(self.state.release_claim("modules/cli-todo", "haiku-1"))
        self.assertTrue(self.state.release_claim("modules/cli-todo", "sonnet-a"))
        self.assertEqual(self.state.claims_public(), [])

    def test_expired_claim_can_be_taken_over(self):
        self.state.claim("sonnet-a", "modules/cli-todo", "baue CLI")
        # Claim kuenstlich in die Vergangenheit setzen, um Ablauf zu simulieren.
        self.state.state["claims"]["modules/cli-todo"]["at"] = "2000-01-01T00:00:00+00:00"
        taken_over = self.state.claim("haiku-1", "modules/cli-todo", "uebernehme")
        self.assertIsNotNone(taken_over)
        self.assertEqual(taken_over["agent_id"], "haiku-1")


if __name__ == "__main__":
    unittest.main()
