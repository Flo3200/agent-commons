"""Tests fuer unpushed_branches.py (nur die reine format_report-Funktion,
kein echtes Git noetig). Ausfuehren mit: python3 -m unittest test_unpushed_branches -v"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from unpushed_branches import format_report


class FormatReportTests(unittest.TestCase):
    def test_empty_list_means_everything_pushed(self):
        text = format_report([], base="origin/main")
        self.assertIn("Alles gepusht", text)
        self.assertIn("origin/main", text)

    def test_lists_branch_with_details(self):
        entries = [{
            "branch": "agent/x/feature",
            "commits_ahead": 2,
            "last_subject": "Feature X",
            "last_author": "sonnet-a",
            "last_date": "2026-09-11",
        }]
        text = format_report(entries)
        self.assertIn("agent/x/feature", text)
        self.assertIn("2 Commits", text)
        self.assertIn("Feature X", text)
        self.assertIn("sonnet-a", text)

    def test_singular_commit_wording(self):
        entries = [{
            "branch": "agent/x/tiny",
            "commits_ahead": 1,
            "last_subject": "Tiny fix",
            "last_author": "a",
            "last_date": "2026-09-11",
        }]
        text = format_report(entries)
        self.assertIn("1 Commit,", text)
        self.assertNotIn("1 Commits", text)

    def test_sorted_alphabetically(self):
        entries = [
            {"branch": "z-branch", "commits_ahead": 1, "last_subject": "", "last_author": "", "last_date": ""},
            {"branch": "a-branch", "commits_ahead": 1, "last_subject": "", "last_author": "", "last_date": ""},
        ]
        text = format_report(entries)
        self.assertLess(text.index("a-branch"), text.index("z-branch"))


if __name__ == "__main__":
    unittest.main()
