# Changelog

Versionierung von **Contract** und **Adaptern** getrennt, damit Strategie und Adapter
unabhängig weiterentwickelt werden können (Versions-Skew vermeiden).

- **Contract:** siehe `docs/modus-contract.md` (Modus-Vokabular). Breaking nur mit Major-Bump.
- **Adapter:** je WR-Familie eigene Versionslinie.

## [Unreleased]

### Geändert
- **0.2C-Ladeleistung automatisch aus der Batteriekapazität** (Register 40187):
  Modus „Akku 0.2C Laden" rechnet jetzt `0,2 × Kapazität` selbst. Neuer Blueprint-Input
  `battery_capacity_sensor` (Default: `sensor.sma_stp_se_40187_batterie_nennkapazitaet`).
  Der manuelle Helfer `input_number.akkusteuerung_02c_ladestaerke` **entfällt**.
  ⚠️ Wer den Adapter aus v1.0.0 importiert hat: alten 0.2C-Helfer entfernen und im
  Blueprint den Kapazitäts-Sensor zuweisen (Default passt meist).
- **Doku auf GUI-first** umgestellt: Helfer per Oberfläche anlegen (mit Hinweis auf exakte
  Entity-IDs); Modbus bleibt YAML (HA hat dafür keine GUI). YAML-Helfer-Datei bleibt als
  Abkürzung erhalten.
- `docs/modbus-register-referenz.md`: Hinweis ergänzt, dass der Blueprint die Variante
  `65535 − P` nutzt (lädt ~1 W mehr als die exakte SMA-Formel `65536 − P`, vernachlässigbar).

### Geplant
- **Write-on-Change**: nur schreiben wenn Wert geändert ODER letzter Write älter als
  Keepalive-Intervall (SMA-Fremdsteuerung läuft sonst aus). Reduziert Modbus-Last.
- `sma_sbs_adapter.yaml` (abweichendes Register-Map, gleicher Contract).
- Capability-Schicht (Adapter meldet Fähigkeiten) – erst mit erstem Nicht-SMA-Adapter.

## [1.0.0] – 2026-06-29 — Erster öffentlicher Stand

Erste öffentliche Veröffentlichung. Der Adapter ist live (Phase 1a) über einen
Tageszyklus erprobt. Nutzung: entweder mit einer **eigenen Strategie**, die
`input_select.akkusteuerung_modus` setzt, oder mit dem Schwesterprojekt
[`ha-opti-akkusteuerung`](https://github.com/Optic00/ha-opti-akkusteuerung).

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
