# Changelog

Versionierung von **Contract** und **Adaptern** getrennt, damit Strategie und Adapter
unabhängig weiterentwickelt werden können (Versions-Skew vermeiden).

- **Contract:** siehe `docs/modus-contract.md` (Modus-Vokabular). Breaking nur mit Major-Bump.
- **Adapter:** je WR-Familie eigene Versionslinie.

## [Unreleased]

### Geplant
- `sma_sbs_adapter.yaml` (abweichendes Register-Map, gleicher Contract).
- Capability-Schicht (Adapter meldet Fähigkeiten) – erst mit erstem Nicht-SMA-Adapter.

## [1.5.0] - 2026-07-02 - Adapter `sma_stp_se`: neuer Modus "Akku Netzladen"

Additives MINOR-Release (Contract-Erweiterung um einen neuen Modus, kein Breaking
Change an bestehenden Modi). Hintergrund: der bisherige Modus "Akku nur Laden"
(`CmpBMS.OpMod` 2289) ist eine reine Entladesperre - Netzbezug entsteht dabei nur,
wenn `BatChaMinW` (Register 40793) manuell auf einen Wert > 0 gesetzt wird. Für
gezieltes, erzwungenes Netzladen (z. B. Negativpreis-Fenster oder Peak-Vorladen in
`ha-opti-akkusteuerung`) fehlte bisher ein eigener Modus.

### Hinzugefügt
- **Neuer Modus `Akku Netzladen`**: schreibt denselben `CmpBMS.OpMod`-Wert `2289`
  wie "Akku nur Laden" (Entladen bleibt gesperrt), setzt aber `BatChaMinW` (40793)
  auf die volle dynamische Ladeleistung (`dyn_charge_entity`) statt sie auf
  `akkusteuerung_min_ladestaerke` zu deckeln. Damit wird die Anlage gezwungen,
  mindestens mit dem dynamisch berechneten Sollwert aus dem Netz zu laden -
  akkuschonend über dieselbe SoC-Taper-/Score-/Temperaturlogik wie im Modus
  "Akku Dynamisch", nur ohne Entlade-Möglichkeit.
- Neue `input_select`-Option `Akku Netzladen` (9. Option) in
  `examples/akkusteuerung_helpers.example.yaml`.
- **Neuer Input `inverter_ok_states`** (Sicherheitsfix, Community-Report): das
  WR-Status-Gate akzeptierte bisher hart nur den Sensorwert `"Ok"`. Meldet der WR
  einen anderen Status (z. B. `2119` = Abregelung wegen der 70%-Einspeisebegrenzung,
  oder einen Code, den ein selbstgebauter Mapping-Helfer nicht kennt), blockierte
  das ALLE Automations-Läufe inklusive Keepalive - die SMA-Fremdsteuerung lief dann
  in ihren Timeout und der WR fiel in seinen internen Modus zurück (lud/entlud
  eigenmächtig, live bestätigt: WR lud mit ~7 kW trotz aktivem Modus "Akku nur
  Entladen"). Das Status-Gate ist jetzt eine konfigurierbare Liste
  (`inverter_ok_states`, Default `["Ok"]`) statt einer hart codierten
  State-Bedingung.

### Geändert
- Blueprint-Beschreibung, README-Optionslisten und `docs/modus-contract.md` um den
  neuen Modus ergänzt.
- WR-Status-Bedingung von `condition: state` (`== "Ok"`) auf `condition: template`
  (`state in inverter_ok_states`) umgestellt.

### Nicht-breaking
- Bestehende Modi (`Akku nur Laden` u. a.) sind unverändert - der neue Modus ist ein
  zusätzlicher `if`-Branch. Wer aktualisiert, muss lediglich die neue
  `input_select`-Option `Akku Netzladen` in seinem Modus-Dropdown ergänzen, um sie
  nutzen zu können; ohne die Option läuft der Adapter wie bisher weiter.
- `inverter_ok_states` hat den Default `["Ok"]` - bei unverändertem Input verhält
  sich das WR-Status-Gate exakt wie vorher.

### Bekanntes offenes Risiko
- Der 500-W-Settling-Deckel aus v1.3.0 (Schutz vor Ladeleistungs-Spikes nach
  Moduswechsel) ist bewusst weiterhin nur an `Akku Dynamisch` gebunden und greift
  NICHT beim Wechsel nach `Akku Netzladen`. Die in v1.3.0 dokumentierte Root Cause
  (interne Ladeleistungsgrenze driftet, solange Laden im aktuellen Modus irrelevant
  ist) betraf denselben Ausgangszustand (Rueckkehr aus einem Nicht-Lade-Modus wie
  "nur Entladen") wie ein Wechsel nach "Akku Netzladen" - ob derselbe Spike auch
  hier auftritt, ist **nicht live verifiziert**. Vor Produktiv-Rollout: Uebergang
  "nur Entladen"/"Pause" -> "Akku Netzladen" gezielt auf Spikes testen (siehe
  `docs/modbus-register-referenz.md`, Abschnitt "Bekannte Probleme & Hinweise").

## [1.3.0] – 2026-07-01 — Adapter `sma_stp_se`: Ladeleistungs-Spike nach Moduswechsel behoben

Additives MINOR-Release (Contract unverändert, keine neuen Inputs). Live beobachtet
und 2x reproduziert: nach längerer Verweildauer in einem Forced-Modus ("nur Entladen")
lädt der WR beim Rücksprung auf "Dynamisch" für ~2:20–2:50 Min mit nahezu Nennleistung
statt dem Sollwert — siehe `docs/modbus-register-referenz.md` Abschnitt "Bekannte
Probleme & Hinweise" für die volle Root-Cause-Analyse.

### Geändert
- **Moduswechsel erzwingt sofortigen Rewrite der BMS-Leistungsgrenzen**
  (40793/40795/40797/40799/40801): der Modus ist jetzt Teil von `current_snapshot`,
  wodurch jeder Wechsel `write_needed` sofort auslöst, statt bis zum nächsten
  Write-on-Change/Keepalive-Zyklus zu warten.
- **Defensiver Sicherheits-Deckel (500 W)** auf die Ladeleistungsgrenze für die ersten
  330s (5:30 Min) nach jedem Eintritt in "Dynamisch", danach automatischer Rücksprung
  auf den echten Sollwert.
- **Registeradresse für "Dynamisch"**: `CmpBMS.OpMod` wird jetzt konsistent über 41259
  (Sunspec) geschrieben statt über die bisherige Alternative 40236 — wie die anderen
  3 Modi und wie in der offiziellen SMA-Support-Antwort dokumentiert.

### Verifiziert
- Live auf Produktivanlage (STP SE 10.0 + BYD HVS 12.8): Ladeleistung blieb im
  kritischen Fenster durchgehend ≤625 W (vorher bis 10.748 W), sauberer Übergang auf
  den echten Sollwert nach Fensterablauf.
- Regressionstest (Pause + Schnell Laden/Entladen bei 500/1000/2000 W): unauffällig.

## [1.4.0] – 2026-07-01 — Adapter `sma_stp_se`: kanonischer Sensor-Default

Additives MINOR-Release (Contract unverändert). Der Default-Wert des Inputs
`dynamic_charge_strength_sensor` wechselt von `sensor.akkusteuerung_dynamische_ladestaerke`
auf den kanonischen Namen `sensor.opti_charge_power_w` (siehe `ha-opti-akkusteuerung`
Canonical-Layer). **Nicht-breaking:** Home Assistant speichert den beim Blueprint-Import
gewählten Wert pro Automations-Instanz — bestehende Automationen sind von der
Default-Änderung nicht betroffen, nur Neuimporte sehen den neuen Vorschlagswert.

### Geändert
- Blueprint-Input `dynamic_charge_strength_sensor`: Default auf `sensor.opti_charge_power_w`,
  Beschreibungstext ergänzt (kanonischer Name bei Nutzung von `ha-opti-akkusteuerung`).

## [1.2.0] – 2026-06-30 — Adapter `sma_stp_se`: Write-on-Change

Additives MINOR-Release (Contract unverändert, neue Inputs haben Defaults). Wer
aus 1.1.0 aktualisiert, muss die zwei neuen Helfer anlegen (siehe README Schritt 2e
bzw. `examples/akkusteuerung_helpers.example.yaml`) — ohne sie nutzt der Adapter
den Fallback "Keepalive abgelaufen" und schreibt wie bisher bei jedem Trigger.

### Geändert
- **Write-on-Change für die BMS-Wertregister** (40793/40795/40797/40799/40801):
  werden nur noch geschrieben, wenn sich der berechnete Wert geändert hat oder der
  letzte Write länger als `keepalive_seconds` (Default 180s, Hersteller-Limit 300s)
  zurückliegt. Reduziert die Modbus-Last bei unveränderten Werten von 5 Writes auf 0.
  Neue Helfer `input_text.akkusteuerung_modbus_letzter_schreibwert` und
  `input_datetime.akkusteuerung_modbus_letzter_schreibzeitpunkt` speichern den
  Zustand persistent (überlebt HA-Neustarts).
- Register 40151 bleibt unverändert immer unconditional geschrieben (kein Teil des
  Write-on-Change-Gates) — verhindert, dass der WR nach „Akku schnell Laden/Entladen"
  fälschlich im Fremdsteuerungs-Modus (`802`) hängen bleibt.
- Bei HA-Start wird das Gate bewusst umgangen (immer geschrieben) — wie bisher,
  unabhängig vom Keepalive-Zustand, da der tatsächliche WR-Zustand nach einem
  Neustart unbekannt ist.
- **Zusätzlicher `/1`-Minuten-Keepalive-Check**: der bisherige `/4`-Minuten-Tick
  allein hätte die Schreib-Lücke bei stabilen Werten auf bis zu `keepalive_seconds +
  240s` anwachsen lassen können — über dem 300s-Hersteller-Limit. Ein feinerer Tick
  prüft jetzt jede Minute, ob der Keepalive abgelaufen ist, bricht den Lauf aber
  sofort ab (kein Modbus-Write), wenn nichts ansteht — und zwar auch in „Akku
  Automatisch"/„schnell Laden"/„schnell Entladen", die den BMS-Gate nie erreichen
  (sonst liefe die Automation dort fälschlich jede Minute statt wie bisher alle
  240s). `keepalive_seconds`-Max deshalb von 280s auf 200s gesenkt
  (Worst-Case-Lücke jetzt ~266s).
- Nach „Akku schnell Laden"/„Akku schnell Entladen" wird beim nächsten
  Standardpfad-Lauf zwangsweise neu geschrieben (Snapshot wird beim Verlassen
  dieser Modi invalidiert) — verhindert, dass die BMS-Wertregister nach dem
  Fremdsteuerungs-Ausflug fälschlich als „unverändert" übersprungen werden.
- Helfer-Updates laufen jetzt mit `continue_on_error`, damit ein noch fehlender
  Helfer (z. B. direkt nach dem Update, bevor die neuen Helfer angelegt wurden)
  nicht zu wiederholten Fehlermeldungen führt.

## [1.1.0] – 2026-06-29 — Adapter `sma_stp_se`: 0.2C automatisch

Additives MINOR-Release (Contract unverändert, neuer Blueprint-Input hat einen Default).
Wer aus 1.0.0 aktualisiert, muss nichts tun, sofern der Kapazitäts-Sensor dem Default
entspricht — der frühere manuelle 0.2C-Helfer wird dann nur überflüssig.

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
