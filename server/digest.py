"""Tages-Digest: fasst Checkins/Proposals/Claims eines Tages kurz zusammen.

Grund: Flo (und neue Agenten) muessen sonst den kompletten Chat-/Aktivitaets-
Verlauf lesen, um zu verstehen was heute passiert ist. build_digest() macht
daraus 5-15 Stichpunkte aus den bereits vorhandenen CommonsState-Daten -
kein neuer Datenspeicher, nur eine Zusammenfassung der bestehenden.
"""
from datetime import datetime, timezone


def _today(day):
    return day or datetime.now(timezone.utc).strftime("%Y-%m-%d")


def build_digest(state, day=None):
    """state: eine CommonsState-Instanz. day: 'YYYY-MM-DD' (Standard: heute, UTC).
    Gibt einen kurzen Markdown-Text zurueck (Stichpunkte, keine Details)."""
    day = _today(day)

    activity = [a for a in state.activity_public(limit=1000) if a["at"].startswith(day)]
    proposals = [p for p in state.proposals_public(limit=1000) if p["at"].startswith(day)]
    claims = state.claims_public()  # nur aktuell aktive, kein Datumsfilter noetig

    agents_today = sorted({a["agent_id"] for a in activity})

    lines = [f"# Tages-Digest {day}", ""]
    lines.append(f"- {len(agents_today)} Agent(en) aktiv: {', '.join(agents_today) or '-'}")
    lines.append(f"- {len(activity)} Check-ins insgesamt")
    lines.append(f"- {len(proposals)} neue Vorschlaege")
    lines.append(f"- {len(claims)} aktive Claims (wer arbeitet gerade woran)")

    if proposals:
        lines.append("")
        lines.append("## Vorschlaege heute")
        for p in proposals:
            lines.append(f"- **{p['author']}**: {p['text']}")

    if claims:
        lines.append("")
        lines.append("## Wer arbeitet woran")
        for c in sorted(claims, key=lambda c: c["name"]):
            note = f" - {c['note']}" if c.get("note") else ""
            lines.append(f"- `{c['name']}`: {c['agent_id']}{note}")

    if activity:
        lines.append("")
        lines.append("## Letzter Status pro Agent (heute)")
        latest = {}
        for a in activity:  # Liste ist chronologisch, letzter Eintrag gewinnt
            latest[a["agent_id"]] = a
        for agent_id in sorted(latest):
            a = latest[agent_id]
            lines.append(f"- **{agent_id}**: {a['status']} - {a['detail']}")

    return "\n".join(lines)
