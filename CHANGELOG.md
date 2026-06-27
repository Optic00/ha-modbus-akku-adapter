# Changelog

Versionierung von **Contract** und **Adaptern** getrennt, damit Strategie und Adapter
unabhängig weiterentwickelt werden können (Versions-Skew vermeiden).

- **Contract:** siehe `docs/modus-contract.md` (Modus-Vokabular). Breaking nur mit Major-Bump.
- **Adapter:** je WR-Familie eigene Versionslinie.

## [Unreleased]

### Hinzugefügt
- Initiales Repo, ausgegliedert aus `ha-opti-akku-blueprint` (Branch `modernisierung`).
- **Contract v1** (`docs/modus-contract.md`): 8 Modi, `input_select.akkusteuerung_modus`.
- **Adapter `sma_stp_se` v1** (`sma_stp_se_adapter.yaml`): SMA STP SE Hybrid, voll
  agnostisch via `!input` (mode_select / modbus_hub / status / dyn. Ladestärke),
  Min<Max-Guard. Migriert aus dem live (Phase 1a) erprobten Stand.
- **dyn. Ladestärke als Trigger** ergänzt: Änderung der dynamischen Ladestärke löst den
  Adapter sofort aus (2 s entprellt), statt erst beim /4-min-Tick → Drosselung greift
  prompt. Ersetzt die provisorische Live-Brücke-Automation (kann nach Deploy entfernt
  werden).
- `docs/modbus-register-referenz.md`, `examples/sma_modbus.example.yaml`.

### Geplant
- **Write-on-Change**: nur schreiben wenn Wert geändert ODER letzter Write älter als
  Keepalive-Intervall (SMA-Fremdsteuerung läuft sonst aus). Reduziert Modbus-Last.
- `sma_sbs_adapter.yaml` (abweichendes Register-Map, gleicher Contract).
- Capability-Schicht (Adapter meldet Fähigkeiten) – erst mit erstem Nicht-SMA-Adapter.
