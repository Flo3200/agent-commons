#!/usr/bin/env python3
"""Zeigt alle lokalen Branches mit Commits, die noch nicht auf origin liegen.

Grund: Agenten haben keinen GitHub-Push-Zugriff in dieser Umgebung, Flo
pusht manuell. Bisher musste er sich das aus einzelnen Chat-Nachrichten
("kannst du Branch X pushen?") zusammensuchen. Dieses Skript listet den
tatsaechlichen Git-Zustand direkt - unabhaengig davon, was irgendwer im
Chat behauptet hat.

Nutzung:
  python3 scripts/unpushed_branches.py [--base origin/main]
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def _run(args):
    return subprocess.run(
        args, cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


def local_branches():
    out = _run(["git", "branch", "--format=%(refname:short)"])
    return [b for b in out.splitlines() if b]


def find_unpushed(base="origin/main"):
    """Gibt eine Liste von Branches zurueck, die Commits haben, die <base>
    nicht hat (also: noch nicht gepusht/gemergt). base-Branch selbst
    wird uebersprungen."""
    results = []
    for branch in local_branches():
        if branch == base.split("/", 1)[-1]:
            continue
        try:
            count = int(_run(["git", "rev-list", "--count", f"{base}..{branch}"]))
        except subprocess.CalledProcessError:
            continue
        if count == 0:
            continue
        last_subject = _run(["git", "log", "-1", "--format=%s", branch])
        last_author = _run(["git", "log", "-1", "--format=%an", branch])
        last_date = _run(["git", "log", "-1", "--format=%ad", "--date=short", branch])
        results.append({
            "branch": branch,
            "commits_ahead": count,
            "last_subject": last_subject,
            "last_author": last_author,
            "last_date": last_date,
        })
    return results


def format_report(entries, base="origin/main"):
    if not entries:
        return f"Alles gepusht - kein lokaler Branch hat Commits vor {base}."
    lines = [f"Ungepushte Branches (gegenueber {base}):", ""]
    for e in sorted(entries, key=lambda e: e["branch"]):
        plural = "Commit" if e["commits_ahead"] == 1 else "Commits"
        lines.append(
            f"- {e['branch']}: {e['commits_ahead']} {plural}, "
            f"zuletzt {e['last_date']} ({e['last_author']}) - \"{e['last_subject']}\""
        )
    lines.append("")
    lines.append("Push mit: git push -u origin <branch>")
    return "\n".join(lines)


def main(argv):
    base = "origin/main"
    if len(argv) >= 2 and argv[0] == "--base":
        base = argv[1]
    print(format_report(find_unpushed(base), base))


if __name__ == "__main__":
    main(sys.argv[1:])
