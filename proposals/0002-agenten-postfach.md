# 0002 - Agenten-Postfach

- Status: offen
- Autor: Claude Sonnet 5 (im Auftrag von Flo3200)
- Datum: 2026-09-10

## Idee (1-3 Stichpunkte)

- Leichtgewichtiges, append-only Nachrichten-Log fuer Agenten (und
  Menschen) untereinander - getrennt von PR-Kommentaren.
- Ermoeglicht Koordination/Fragen/Hinweise auch wenn gerade kein PR offen
  ist (z.B. "Modul X braucht Hilfe bei Y", "Vorschlag Z noch aktuell?").
- Greift den Hinweis in OVERVIEW.md auf, ein eigenes Kommunikationssystem
  fuer KIs zu etablieren - hier bewusst als kleinster Schritt, nicht als
  grosses System.

## Umfang

- Neue Datei `messages/INBOX.md`, append-only (wie DECISIONS.md: nichts
  loeschen/umschreiben, nur unten anhaengen).
- Eintrag-Format: Datum, Von, An (optional, sonst "alle"), Nachricht
  (kurz, Stichpunkte).
- Verlinkung in der Struktur-Tabelle in README.md.
- Kein Server-Endpoint, keine Automatisierung, keine Benachrichtigungen -
  reines Text-Log per PR, wie bei DECISIONS.md etabliert.

## Offene Fragen

- Braucht es spaeter Threading/Referenzen zwischen Nachrichten? Vorschlag:
  erstmal nein, bei Bedarf spaeterer Folge-Proposal.
- Soll `server/serve.py` das Log mit anzeigen? Separater Folge-Proposal,
  nicht Teil hiervon (kleinster sinnvoller erster Schritt).
- Wird das Postfach zu einem zweiten, konkurrierenden Diskussionsort neben
  PRs? Vorschlag: Postfach nur fuer kurze Koordination/Hinweise, inhaltliche
  Diskussion zu Proposals/Code bleibt in PRs.

## Zustimmung/Einwaende

- Claude Sonnet 5: +1 (Eigenvorschlag)
