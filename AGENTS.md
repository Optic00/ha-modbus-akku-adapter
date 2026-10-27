# Hinweise für Coding-Agenten

## Projekt

Dieses Repo enthält Home-Assistant-Blueprints, die Steuerungsmodi in
Modbus-Schreibbefehle für Batterie-Hybrid-Wechselrichter übersetzen.
Der vorhandene Adapter unterstützt SMA STP SE Hybrid.
Vor der Arbeit `README.md` und `CHANGELOG.md` lesen.

## Regeln

- Schreibsperren und den Modus-Contract in `docs/modus-contract.md` niemals
  abschwächen. Die Single-Writer-Regel erhalten.
- Keine Messlogs mit personenbezogenen oder sensiblen Daten committen:
  IP-Adressen, Seriennummern, Tokens, E-Mail-Adressen oder Standorte.
- Vor Änderungen `python3 -m pytest tests/` ausführen und Fehler melden.
- `CHANGELOG.md` im Keep-a-Changelog-Stil unter `[Unreleased]` aktuell halten.
- GitHub Actions ausschließlich auf vollständige Commit-SHAs pinnen.
- KI-geschriebene PRs brauchen ein Review durch eine andere Modellfamilie
  als die des Autors.
- Nicht direkt auf `main` pushen.
