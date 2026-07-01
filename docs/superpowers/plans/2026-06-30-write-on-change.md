# Write-on-Change Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Die fünf BMS-Wertregister (40793/40795/40797/40799/40801) im Standardpfad von `sma_stp_se_adapter.yaml` nur noch schreiben, wenn sich der berechnete Wert geändert hat oder der letzte Write älter als ein konfigurierbares Keepalive-Intervall ist — statt wie bisher bei jedem Trigger unconditional.

**Architecture:** Zwei neue Blueprint-Inputs (`input_text`-Snapshot-Helfer, `input_datetime`-Zeitstempel-Helfer) plus ein `number`-Input (`keepalive_seconds`) speichern den zuletzt geschriebenen Zustand persistent über Automation-Läufe und HA-Neustarts hinweg. Ein `if/then`-Gate um die fünf Wertregister vergleicht den aktuellen Soll-Snapshot gegen den gespeicherten; Register 40151 bleibt davon unberührt und wird weiterhin immer geschrieben. Der `homeassistant: start`-Trigger bekommt eine `id`, damit er das Gate gezielt umgehen kann.

**Tech Stack:** Home Assistant Automation-Blueprint (YAML + Jinja2-Templates), keine Programmiersprache, kein CI/Testframework im Repo.

## Global Constraints

- Bestehende v1.1.0-Importe dürfen beim Update nicht brechen → alle neuen Inputs brauchen Defaults (siehe Spec, Abschnitt „State-Storage").
- Hersteller-Limit für die BMS-Register: max. alle 300s schreiben (`docs/modbus-register-referenz.md:112`) → `keepalive_seconds`-Selector-Max ist **200** (nach dem Nachtrag vom finalen Review — ursprünglich 280, aber das ließ in Kombination mit dem `/4`-Tick eine Lücke von bis zu ~520s zu; siehe Task 6).
- Register 40151 wird **immer** unconditional geschrieben, niemals Teil des Write-on-Change-Gates (siehe Spec, Abschnitt „Scope").
- Snapshot-Format: Pipe-getrennter String aus den vier berechneten Werten + fixer `0` für 40801: `"{{ v_40793 }}|{{ v_40795 }}|{{ v_40797 }}|{{ v_40799 }}|0"`.
- `mode: single` bleibt unverändert (kein `restart`/`queued`).
- Helfer-Update-Reihenfolge nach den Writes: erst `input_datetime.set_datetime`, dann `input_text.set_value`.
- Vollständige Spec: `docs/superpowers/specs/2026-06-30-write-on-change-design.md`.

---

## Datei-Übersicht

- **Modify:** `blueprints/automation/akku_adapter/sma_stp_se_adapter.yaml` — neue Inputs, neue Variablen, Trigger-ID, Standardpfad-Block umgebaut.
- **Modify:** `examples/akkusteuerung_helpers.example.yaml` — zwei neue Helfer ergänzt.
- **Modify:** `README.md` — neue Helfer in Schritt 2 dokumentiert.
- **Modify:** `CHANGELOG.md` — `[1.2.0]`-Eintrag.

Da es sich um ein deklaratives YAML-Blueprint ohne Programmlogik-Tests handelt, ersetzt **YAML-Syntaxvalidierung** (`python3 -c "import yaml; yaml.safe_load(open(...))"`) die klassischen Unit-Tests pro Schritt. Der abschließende Funktionstest erfolgt manuell am Live-System (Task 6).

---

### Task 1: Neue Blueprint-Inputs ergänzen

**Files:**
- Modify: `blueprints/automation/akku_adapter/sma_stp_se_adapter.yaml:58-67` (nach dem `mode_select`-Input)

**Interfaces:**
- Produces: Inputs `last_write_value_helper`, `last_write_time_helper`, `keepalive_seconds`, abrufbar in späteren Tasks via `!input <name>`.

- [ ] **Step 1: Aktuellen Input-Block lesen**

Lies `blueprints/automation/akku_adapter/sma_stp_se_adapter.yaml` Zeilen 1-70, um den exakten Kontext vor der Änderung zu bestätigen (Datei kann sich seit Planerstellung nicht geändert haben, aber zur Sicherheit prüfen).

- [ ] **Step 2: Drei neue Inputs einfügen**

Füge direkt nach dem `mode_select`-Input-Block (endet mit `domain: input_select`, vor der Zeile `variables:`) folgenden YAML-Block ein (Einrückung: zwei Leerzeichen unter `input:`, identisch zu den bestehenden Inputs):

```yaml
    last_write_value_helper:
      name: "Helfer: Letzter Schreibwert (Write-on-Change)"
      description: >
        input_text-Helfer, der den Snapshot der zuletzt geschriebenen BMS-Wertregister
        speichert (40793/40795/40797/40799/40801). Wird vom Adapter automatisch
        gepflegt, nicht manuell setzen. Siehe examples/akkusteuerung_helpers.example.yaml.
      default: input_text.akkusteuerung_modbus_letzter_schreibwert
      selector:
        entity:
          domain: input_text

    last_write_time_helper:
      name: "Helfer: Letzter Schreibzeitpunkt (Write-on-Change)"
      description: >
        input_datetime-Helfer (Datum + Uhrzeit), der den Zeitpunkt des letzten
        tatsächlichen BMS-Register-Schreibvorgangs speichert. Wird vom Adapter
        automatisch gepflegt. Siehe examples/akkusteuerung_helpers.example.yaml.
      default: input_datetime.akkusteuerung_modbus_letzter_schreibzeitpunkt
      selector:
        entity:
          domain: input_datetime

    keepalive_seconds:
      name: "Keepalive-Intervall (Sekunden)"
      description: >
        Maximales Intervall, nach dem die BMS-Wertregister (40793-40801) auch ohne
        Wertänderung erneut geschrieben werden (sonst läuft die SMA-Fremdsteuerung
        aus). Hersteller-Limit: 300s. Default 180s lässt Sicherheitsmarge.
      default: 180
      selector:
        number:
          min: 30
          max: 280
          step: 10
          unit_of_measurement: s
          mode: box
```

- [ ] **Step 3: YAML-Syntax validieren**

Run: `python3 -c "import yaml; yaml.safe_load(open('blueprints/automation/akku_adapter/sma_stp_se_adapter.yaml'))" && echo OK`
Expected: `OK` (kein Traceback)

- [ ] **Step 4: Commit**

```bash
git add blueprints/automation/akku_adapter/sma_stp_se_adapter.yaml
git commit -m "$(cat <<'EOF'
sma_stp_se: neue Inputs fuer Write-on-Change (Snapshot/Timestamp/Keepalive)

Noch ohne Verhaltensaenderung - die Inputs werden in den naechsten Schritten
in variables: und den Standardpfad-Block verdrahtet.
EOF
)"
```

---

### Task 2: Trigger-ID für HA-Start ergänzen

**Files:**
- Modify: `blueprints/automation/akku_adapter/sma_stp_se_adapter.yaml:93-94` (`triggers:`-Block, letzter Eintrag)

**Interfaces:**
- Produces: Trigger-ID `ha_start`, abrufbar in Task 3 via `trigger.id == 'ha_start'`.

- [ ] **Step 1: Trigger-Eintrag erweitern**

Ändere:

```yaml
  - event: start
    trigger: homeassistant
```

zu:

```yaml
  - event: start
    trigger: homeassistant
    id: ha_start
```

- [ ] **Step 2: YAML-Syntax validieren**

Run: `python3 -c "import yaml; yaml.safe_load(open('blueprints/automation/akku_adapter/sma_stp_se_adapter.yaml'))" && echo OK`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add blueprints/automation/akku_adapter/sma_stp_se_adapter.yaml
git commit -m "sma_stp_se: Trigger-ID fuer HA-Start ergaenzt (fuer Write-on-Change-Bypass)"
```

---

### Task 3: Variablen für Snapshot/Keepalive-Vergleich

**Files:**
- Modify: `blueprints/automation/akku_adapter/sma_stp_se_adapter.yaml:69-72` (`variables:`-Block)

**Interfaces:**
- Consumes: Inputs aus Task 1 (`last_write_value_helper`, `last_write_time_helper`, `keepalive_seconds`), Trigger-ID `ha_start` aus Task 2.
- Produces: Variablen `snapshot_helper`, `timestamp_helper`, `keepalive_s`, `v_40793`, `v_40795`, `v_40797`, `v_40799`, `current_snapshot`, `write_needed` — alle in Task 4 verwendet.

- [ ] **Step 1: `variables:`-Block ersetzen**

Ersetze den kompletten bestehenden Block:

```yaml
variables:
  # !input ist in Jinja nicht direkt verfügbar – erst als Variable exponieren.
  dyn_charge_entity: !input dynamic_charge_strength_sensor
  capacity_entity: !input battery_capacity_sensor
```

durch:

```yaml
variables:
  # !input ist in Jinja nicht direkt verfügbar – erst als Variable exponieren.
  dyn_charge_entity: !input dynamic_charge_strength_sensor
  capacity_entity: !input battery_capacity_sensor
  snapshot_helper: !input last_write_value_helper
  timestamp_helper: !input last_write_time_helper
  keepalive_s: !input keepalive_seconds
  v_40793: "{{ [states('input_number.akkusteuerung_min_ladestaerke') | int(0), states(dyn_charge_entity) | int(0)] | min }}"
  v_40795: "{{ states(dyn_charge_entity) | int(0) }}"
  v_40797: "{{ [states('input_number.akkusteuerung_min_entladestaerke') | int(0), states('input_number.akkusteuerung_max_entladestaerke') | int(0)] | min }}"
  v_40799: "{{ states('input_number.akkusteuerung_max_entladestaerke') | int(0) }}"
  current_snapshot: "{{ [v_40793, v_40795, v_40797, v_40799, 0] | join('|') }}"
  write_needed: >-
    {% set valid_dt = state_attr(timestamp_helper, 'has_date') and state_attr(timestamp_helper, 'has_time') %}
    {% set last_ts = as_timestamp(states(timestamp_helper), none) if valid_dt else none %}
    {{ trigger.id == 'ha_start'
       or current_snapshot != states(snapshot_helper)
       or last_ts is none
       or (now().timestamp() - last_ts) > (keepalive_s | int(0)) }}
```

Hinweis: `v_40793`/`v_40797` übernehmen exakt die bisherigen Inline-Templates aus dem
Standardpfad (Min-Guard gegen `40795`/`40799`) — keine Logikänderung, nur Extraktion
in benannte Variablen.

- [ ] **Step 2: YAML-Syntax validieren**

Run: `python3 -c "import yaml; yaml.safe_load(open('blueprints/automation/akku_adapter/sma_stp_se_adapter.yaml'))" && echo OK`
Expected: `OK`

- [ ] **Step 3: Jinja-Template isoliert prüfen**

Da kein HA-Testserver verfügbar ist, das `write_needed`-Template syntaktisch mit Jinja2 direkt prüfen (fängt Tippfehler/Klammerfehler ab, nicht HA-spezifische Funktionen wie `states()`):

```bash
python3 -c "
from jinja2 import Environment
env = Environment()
tpl = '''{% set valid_dt = state_attr(timestamp_helper, 'has_date') and state_attr(timestamp_helper, 'has_time') %}
{% set last_ts = as_timestamp(states(timestamp_helper), none) if valid_dt else none %}
{{ trigger.id == 'ha_start' or current_snapshot != states(snapshot_helper) or last_ts is none or (now().timestamp() - last_ts) > (keepalive_s | int(0)) }}'''
env.parse(tpl)
print('OK: Jinja-Syntax gueltig')
"
```

Expected: `OK: Jinja-Syntax gueltig` (Parse-Fehler würden als `TemplateSyntaxError` auftauchen)

- [ ] **Step 4: Commit**

```bash
git add blueprints/automation/akku_adapter/sma_stp_se_adapter.yaml
git commit -m "$(cat <<'EOF'
sma_stp_se: Snapshot/Keepalive-Variablen fuer Write-on-Change

Berechnet current_snapshot und write_needed; noch nicht im Standardpfad
verdrahtet (folgt in naechstem Commit).
EOF
)"
```

---

### Task 4: Standardpfad-Block umbauen (Gate + Helfer-Update)

**Files:**
- Modify: `blueprints/automation/akku_adapter/sma_stp_se_adapter.yaml:182-243` (Standardpfad-Block)

**Interfaces:**
- Consumes: Variablen aus Task 3 (`write_needed`, `v_40793`, `v_40795`, `v_40797`, `v_40799`, `current_snapshot`, `snapshot_helper`, `timestamp_helper`).

- [ ] **Step 1: Standardpfad-Block ersetzen**

Ersetze den kompletten Block von `# --- Standardpfad: Modbus-Basis-Parameter setzen ---` bis zum letzten `action: modbus.write_register` vor `- alias: Bei "Akku Pause"` (aktuell Zeilen 182-243):

```yaml
  # --- Standardpfad: Modbus-Basis-Parameter setzen ---
  - data:
      hub: !input modbus_hub
      address: 40151
      slave: 3
      value:
        - 0
        - 803
    action: modbus.write_register
  - delay:
      seconds: 1
  - data:
      hub: !input modbus_hub
      address: 40793
      slave: 3
      value:
        - 0
        # Min-Ladestärke nie über die dynamische Max-Ladestärke (40795) → kein Min>Max an die BMS
        - "{{ [states('input_number.akkusteuerung_min_ladestaerke') | int(0), states(dyn_charge_entity) | int(0)] | min }}"
    action: modbus.write_register
  - delay:
      seconds: 1
  - alias: Schreib die dynamische Ladestärke auf Modbus
    data:
      hub: !input modbus_hub
      address: 40795
      slave: 3
      value:
        - 0
        - "{{ states(dyn_charge_entity) | int(0) }}"
    action: modbus.write_register
  - delay:
      seconds: 1
  - data:
      hub: !input modbus_hub
      address: 40797
      slave: 3
      value:
        - 0
        # Min-Entladestärke nie über die Max-Entladestärke (40799) → kein Min>Max an die BMS
        - "{{ [states('input_number.akkusteuerung_min_entladestaerke') | int(0), states('input_number.akkusteuerung_max_entladestaerke') | int(0)] | min }}"
    action: modbus.write_register
  - delay:
      seconds: 1
  - data:
      hub: !input modbus_hub
      address: 40799
      slave: 3
      value:
        - 0
        - "{{ states('input_number.akkusteuerung_max_entladestaerke') | int }}"
    action: modbus.write_register
  - delay:
      seconds: 1
  - data:
      hub: !input modbus_hub
      address: 40801
      slave: 3
      value:
        - 0
        - 0
    action: modbus.write_register
```

durch:

```yaml
  # --- Standardpfad: Fremdsteuerung aktivieren (immer, kein Write-on-Change) ---
  - data:
      hub: !input modbus_hub
      address: 40151
      slave: 3
      value:
        - 0
        - 803
    action: modbus.write_register
  - delay:
      seconds: 1

  # --- BMS-Wertregister: nur bei Aenderung oder abgelaufenem Keepalive schreiben ---
  - if:
      - condition: template
        value_template: "{{ write_needed }}"
    then:
      - data:
          hub: !input modbus_hub
          address: 40793
          slave: 3
          value:
            - 0
            - "{{ v_40793 }}"
        action: modbus.write_register
      - delay:
          seconds: 1
      - alias: Schreib die dynamische Ladestärke auf Modbus
        data:
          hub: !input modbus_hub
          address: 40795
          slave: 3
          value:
            - 0
            - "{{ v_40795 }}"
        action: modbus.write_register
      - delay:
          seconds: 1
      - data:
          hub: !input modbus_hub
          address: 40797
          slave: 3
          value:
            - 0
            - "{{ v_40797 }}"
        action: modbus.write_register
      - delay:
          seconds: 1
      - data:
          hub: !input modbus_hub
          address: 40799
          slave: 3
          value:
            - 0
            - "{{ v_40799 }}"
        action: modbus.write_register
      - delay:
          seconds: 1
      - data:
          hub: !input modbus_hub
          address: 40801
          slave: 3
          value:
            - 0
            - 0
        action: modbus.write_register
      - action: input_datetime.set_datetime
        target:
          entity_id: "{{ timestamp_helper }}"
        data:
          timestamp: "{{ now().timestamp() }}"
      - action: input_text.set_value
        target:
          entity_id: "{{ snapshot_helper }}"
        data:
          value: "{{ current_snapshot }}"
```

Wichtig: Die Min-Guard-Kommentare ("Min-Ladestärke nie über...") sind jetzt in Task 3
bei der Definition von `v_40793`/`v_40797` zu finden, nicht mehr inline hier — beim
Ersetzen nicht versehentlich doppelt einfügen.

- [ ] **Step 2: YAML-Syntax validieren**

Run: `python3 -c "import yaml; yaml.safe_load(open('blueprints/automation/akku_adapter/sma_stp_se_adapter.yaml'))" && echo OK`
Expected: `OK`

- [ ] **Step 3: Restliche Branches auf Unverändertheit prüfen**

Run: `git diff blueprints/automation/akku_adapter/sma_stp_se_adapter.yaml -- | grep -E '^[-+]' | grep -v '^+++\|^---'`
Erwartet: Nur Zeilen innerhalb des Standardpfad-Blocks (40151 bis 40801) verändert. Die
Branches "Akku Pause"/"nur Laden"/"nur Entladen"/"Dynamisch"/"0.2C Laden" (Zeilen ab
~245) sowie die früheren `stop:`-Branches dürfen NICHT im Diff auftauchen.

- [ ] **Step 4: Commit**

```bash
git add blueprints/automation/akku_adapter/sma_stp_se_adapter.yaml
git commit -m "$(cat <<'EOF'
sma_stp_se: Write-on-Change fuer BMS-Wertregister aktiv

40151 bleibt unconditional, 40793/40795/40797/40799/40801 nur noch bei
Snapshot-Aenderung oder abgelaufenem Keepalive. HA-Start umgeht das Gate
ueber trigger.id == 'ha_start'.
EOF
)"
```

---

### Task 5: Helfer-Beispieldatei, README, CHANGELOG

**Files:**
- Modify: `examples/akkusteuerung_helpers.example.yaml:34-35` (vor `input_number:`)
- Modify: `README.md` (Schritt 2, nach Zeile 122 / vor `### Schritt 3`)
- Modify: `CHANGELOG.md:9-16` (`[Unreleased]`-Block)

**Interfaces:**
- Keine — reine Dokumentation, keine Code-Schnittstellen.

- [ ] **Step 1: Neue Helfer in `examples/akkusteuerung_helpers.example.yaml` ergänzen**

Füge vor der Zeile `input_number:` (aktuell Zeile 35) folgenden Block ein:

```yaml
input_text:
  # Speichert den Snapshot der zuletzt geschriebenen BMS-Wertregister
  # (Write-on-Change, ab v1.2.0). Wird vom Adapter automatisch gepflegt,
  # nicht manuell befuellen.
  akkusteuerung_modbus_letzter_schreibwert:
    name: Akkusteuerung Modbus Letzter Schreibwert
    max: 255

input_datetime:
  # Zeitpunkt des letzten tatsaechlichen BMS-Register-Schreibvorgangs
  # (Write-on-Change, ab v1.2.0). Wird vom Adapter automatisch gepflegt.
  akkusteuerung_modbus_letzter_schreibzeitpunkt:
    name: Akkusteuerung Modbus Letzter Schreibzeitpunkt
    has_date: true
    has_time: true

```

- [ ] **Step 2: YAML-Syntax der Beispieldatei validieren**

Run: `python3 -c "import yaml; yaml.safe_load(open('examples/akkusteuerung_helpers.example.yaml'))" && echo OK`
Expected: `OK`

- [ ] **Step 3: README Schritt 2 um neue Helfer ergänzen**

Füge nach Zeile 122 (`> dort sind die Entity-IDs garantiert korrekt.`) und vor
`### Schritt 3 – Strategie, die das Dropdown umschaltet` folgenden Abschnitt ein:

```markdown
**e) Zwei Helfer für Write-on-Change (ab v1.2.0)** – der Adapter schreibt die
BMS-Wertregister jetzt nur noch bei Änderung oder abgelaufenem Keepalive. Dafür
braucht er zwei Helfer, die er selbst pflegt (nichts manuell eintragen):

| Typ | Name eintippen | ergibt Entity-ID |
|---|---|---|
| „Text" | `Akkusteuerung Modbus Letzter Schreibwert` | `input_text.akkusteuerung_modbus_letzter_schreibwert` |
| „Datum und Uhrzeit" | `Akkusteuerung Modbus Letzter Schreibzeitpunkt` | `input_datetime.akkusteuerung_modbus_letzter_schreibzeitpunkt` |

Auch hier gilt: per Copy-Paste aus
[`examples/akkusteuerung_helpers.example.yaml`](examples/akkusteuerung_helpers.example.yaml)
geht es schneller als per GUI.
```

- [ ] **Step 4: CHANGELOG.md aktualisieren**

Ersetze den `[Unreleased]`-Block:

```markdown
## [Unreleased]

### Geplant
- **Write-on-Change**: nur schreiben wenn Wert geändert ODER letzter Write älter als
  Keepalive-Intervall (SMA-Fremdsteuerung läuft sonst aus). Reduziert Modbus-Last.
- `sma_sbs_adapter.yaml` (abweichendes Register-Map, gleicher Contract).
- Capability-Schicht (Adapter meldet Fähigkeiten) – erst mit erstem Nicht-SMA-Adapter.
```

durch:

```markdown
## [Unreleased]

### Geplant
- `sma_sbs_adapter.yaml` (abweichendes Register-Map, gleicher Contract).
- Capability-Schicht (Adapter meldet Fähigkeiten) – erst mit erstem Nicht-SMA-Adapter.

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
```

- [ ] **Step 5: YAML/Markdown-Dateien final auf Konsistenz prüfen**

Run: `python3 -c "import yaml; yaml.safe_load(open('examples/akkusteuerung_helpers.example.yaml'))" && echo OK`
Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git add examples/akkusteuerung_helpers.example.yaml README.md CHANGELOG.md
git commit -m "$(cat <<'EOF'
Doku/Beispieldatei fuer Write-on-Change (v1.2.0)

Neue Helfer in der Beispieldatei und README Schritt 2 ergaenzt, CHANGELOG-
Eintrag aus "Geplant" in [1.2.0] ueberfuehrt.
EOF
)"
```

---

### Task 6: Sicherheitsfixes aus finalem Review

**Files:**
- Modify: `blueprints/automation/akku_adapter/sma_stp_se_adapter.yaml`

**Interfaces:**
- Consumes: `write_needed`, `snapshot_helper`, `timestamp_helper` aus Task 3; die Branches "Wenn Akku schnell Laden"/"Wenn Akku schnell Entladen" aus Task 4 (unverändert sonst); die Helfer-Update-Aktionen im Standardpfad-Gate aus Task 4.

Hintergrund: Der finale Whole-Branch-Review (nach Task 5) fand eine Critical- und
zwei Important-Regressionen, von Opus- und Codex-Gegenchecks bestätigt und deren
Fix-Design ebenfalls von beiden verifiziert (siehe Spec-Nachtrag vom 2026-06-30).
Diese Task setzt das verifizierte Fix-Design um.

- [ ] **Step 1: Neuen Keepalive-Tick-Trigger ergänzen**

Füge im `triggers:`-Block, nach dem bestehenden `minutes: /4`-Eintrag und vor dem
`event: start`-Eintrag, folgenden neuen Trigger ein:

```yaml
  - minutes: /1
    trigger: time_pattern
    id: keepalive_check
```

- [ ] **Step 2: Skip-Condition ergänzen**

Ändere den `conditions:`-Block von:

```yaml
conditions:
  - condition: state
    entity_id: !input inverter_status_sensor
    state: "Ok"
```

zu:

```yaml
conditions:
  - condition: state
    entity_id: !input inverter_status_sensor
    state: "Ok"
  - condition: template
    value_template: "{{ not (trigger.id == 'keepalive_check' and not write_needed) }}"
```

Diese Bedingung lässt den gesamten Automation-Lauf nur dann abbrechen, wenn er vom
neuen `/1`-Tick ausgelöst wurde UND nichts zu schreiben ansteht — alle anderen
Trigger (State-Change, `/4`-Tick, HA-Start) sind davon unberührt, weil
`trigger.id == 'keepalive_check'` für sie nie wahr ist.

- [ ] **Step 3: `keepalive_seconds`-Selector-Max senken**

In den Blueprint-Inputs (aus Task 1), ändere im `keepalive_seconds`-Input:

```yaml
      selector:
        number:
          min: 30
          max: 280
          step: 10
          unit_of_measurement: s
          mode: box
```

zu (nur `max` ändert sich, von `280` auf `200`):

```yaml
      selector:
        number:
          min: 30
          max: 200
          step: 10
          unit_of_measurement: s
          mode: box
```

Passe auch die `description:` des Inputs an: "Default 180s lässt Sicherheitsmarge."
bleibt korrekt (180 < 200), keine Änderung nötig dort.

- [ ] **Step 4: Snapshot-Invalidierung in "Wenn Akku schnell Laden" ergänzen**

In der `then:`-Liste der `alias: Wenn Akku schnell Laden`-Branch, füge direkt vor
`- stop: fertig` folgende Aktion ein:

```yaml
      - action: input_text.set_value
        continue_on_error: true
        target:
          entity_id: "{{ snapshot_helper }}"
        data:
          value: ""
```

- [ ] **Step 5: Snapshot-Invalidierung in "Wenn Akku schnell Entladen" ergänzen**

Identische Aktion, direkt vor dem `- stop: fertig` der `alias: Wenn Akku schnell
Entladen`-Branch:

```yaml
      - action: input_text.set_value
        continue_on_error: true
        target:
          entity_id: "{{ snapshot_helper }}"
        data:
          value: ""
```

- [ ] **Step 6: `continue_on_error` an den bestehenden Helfer-Updates ergänzen**

Im Standardpfad-Gate (aus Task 4), ändere die beiden bestehenden Aktionen von:

```yaml
      - action: input_datetime.set_datetime
        target:
          entity_id: "{{ timestamp_helper }}"
        data:
          timestamp: "{{ now().timestamp() }}"
      - action: input_text.set_value
        target:
          entity_id: "{{ snapshot_helper }}"
        data:
          value: "{{ current_snapshot }}"
```

zu:

```yaml
      - action: input_datetime.set_datetime
        continue_on_error: true
        target:
          entity_id: "{{ timestamp_helper }}"
        data:
          timestamp: "{{ now().timestamp() }}"
      - action: input_text.set_value
        continue_on_error: true
        target:
          entity_id: "{{ snapshot_helper }}"
        data:
          value: "{{ current_snapshot }}"
```

- [ ] **Step 7: YAML-Syntax validieren**

Run: `python3 << 'PYEOF'
import yaml
def input_constructor(loader, node):
    return f"!input {node.value}"
yaml.add_constructor('!input', input_constructor, Loader=yaml.SafeLoader)
with open('blueprints/automation/akku_adapter/sma_stp_se_adapter.yaml') as f:
    yaml.safe_load(f)
print("OK")
PYEOF`
Expected: `OK`

- [ ] **Step 8: Scope-Diff prüfen**

Run: `git diff` gegen den vorherigen Commit und bestätige: nur die in Steps 1-6
genannten Stellen geändert (neuer Trigger, neue Condition, `max: 200`, zwei neue
Snapshot-Invalidierungs-Aktionen, vier `continue_on_error: true`-Ergänzungen).
Nichts an den Registerwerten, Delays oder der Schreibreihenfolge geändert.

- [ ] **Step 9: Commit**

```bash
git add blueprints/automation/akku_adapter/sma_stp_se_adapter.yaml
git commit -m "$(cat <<'EOF'
sma_stp_se: Sicherheitsfixes aus finalem Review (Keepalive-Luecke, BMS-Register nach Schnellmodus, Fehler-Spam)

Critical: /1-Keepalive-Tick mit Skip-Bedingung schliesst die Luecke, die der
reine /4-Tick + Write-on-Change-Gate aufreissen konnte (bis zu ~520s statt
300s-Limit). keepalive_seconds-Max von 280 auf 200 gesenkt.

Important: Snapshot-Invalidierung in schnell-Laden/Entladen erzwingt Rewrite
der BMS-Wertregister nach Rueckkehr in den Standardpfad. continue_on_error
an allen Helfer-Updates verhindert Fehler-Spam bei fehlenden Helfern auf
unmigrierten Systemen.

Design von Opus-Subagent und Codex CLI unabhaengig verifiziert, siehe
docs/superpowers/specs/2026-06-30-write-on-change-design.md (Nachtrag).
EOF
)"
```

---

### Task 6b: Mode-gated Keepalive-Skip (Fix für Fix-1-Nebenwirkung)

**Files:**
- Modify: `blueprints/automation/akku_adapter/sma_stp_se_adapter.yaml`

**Interfaces:**
- Consumes: `write_needed` aus Task 3; die neue `keepalive_check`-Trigger-ID und
  Skip-Condition aus Task 6 (wird hier erweitert, nicht ersetzt).

Hintergrund: Der wiederholte finale Whole-Branch-Review (nach Task 6) fand, dass
Fix 1 selbst eine Nebenwirkung hat: `write_needed` wird nur im Standardpfad-Gate
aktualisiert; in „Akku Automatisch"/„Akku schnell Laden"/„Akku schnell Entladen"
(die VOR dem Standardpfad `stop:`en) bleibt `write_needed` dauerhaft `true`, der
neue `/1`-Tick überspringt dort folglich nie — die Automation läuft im
Default-Modus „Automatisch" jetzt alle 60s statt alle 240s. Von Opus-Subagent und
Codex unabhängig verifiziertes Fix-Design (siehe Spec-Nachtrag 2 vom 2026-06-30).

- [ ] **Step 1: Zwei neue Variablen ergänzen**

Füge im `variables:`-Block (nach `keepalive_s: !input keepalive_seconds`, vor
`v_40793: ...`) folgende zwei Zeilen ein:

```yaml
  mode_select_entity: !input mode_select
  early_stop_modes: ['Akku Automatisch', 'Akku schnell Laden', 'Akku schnell Entladen']
```

- [ ] **Step 2: Skip-Condition erweitern**

Ändere die in Task 6 hinzugefügte Condition von:

```yaml
  - condition: template
    value_template: "{{ not (trigger.id == 'keepalive_check' and not write_needed) }}"
```

zu (positive Formulierung, logisch äquivalent erweitert um die Modus-Prüfung):

```yaml
  - condition: template
    value_template: >-
      {{ trigger.id != 'keepalive_check'
         or (states(mode_select_entity) not in early_stop_modes and write_needed) }}
```

- [ ] **Step 3: YAML-Syntax validieren**

Run: `python3 << 'PYEOF'
import yaml
def input_constructor(loader, node):
    return f"!input {node.value}"
yaml.add_constructor('!input', input_constructor, Loader=yaml.SafeLoader)
with open('blueprints/automation/akku_adapter/sma_stp_se_adapter.yaml') as f:
    yaml.safe_load(f)
print("OK")
PYEOF`
Expected: `OK`

- [ ] **Step 4: Scope-Diff prüfen**

Run: `git diff` gegen den vorherigen Commit und bestätige: nur die zwei neuen
Variablen und die geänderte Condition betroffen. Die Trigger-Definition, der
`keepalive_seconds`-Selector, die Snapshot-Invalidierungs-Aktionen und die
`continue_on_error`-Ergänzungen aus Task 6 bleiben unverändert.

- [ ] **Step 5: Commit**

```bash
git add blueprints/automation/akku_adapter/sma_stp_se_adapter.yaml
git commit -m "$(cat <<'EOF'
sma_stp_se: /1-Keepalive-Tick auf Standardpfad-Modi begrenzen

Fix einer Nebenwirkung aus dem vorigen Sicherheitsfix: write_needed bleibt in
Automatisch/schnell-Laden/schnell-Entladen dauerhaft true (Timestamp wird dort
nie aktualisiert), wodurch der /1-Tick nie skippte -> 4x Last im Default-Modus.
Neue early_stop_modes-Variable + erweiterte Skip-Condition beheben das; der
bestehende /4-Tick uebernimmt fuer diese drei Modi weiterhin die Auffrischung,
unveraendert zum Stand vor Write-on-Change.

Design von Opus-Subagent und Codex CLI unabhaengig verifiziert, siehe
docs/superpowers/specs/2026-06-30-write-on-change-design.md (Nachtrag 2).
EOF
)"
```

---

### Task 7: Manuelle Verifikation (Live-System)

**Files:** keine Code-Änderungen — reine Verifikationsschritte.

Dieses Repo hat kein CI/Testframework und keinen simulierten Modbus-Hub; die
folgenden Schritte erfordern Zugriff auf eine echte Home-Assistant-Instanz mit
SMA STP SE Hybrid-WR (oder mindestens einen Modbus-Simulator). **Diese Schritte
kann ein Coding-Agent ohne Hardware-Zugriff nicht selbst ausführen** — sie sind
hier dokumentiert, damit der Nutzer (oder ein Agent mit HA-Zugriff) sie manuell
durchgeht, bevor `git push` erfolgt.

- [ ] **Step 1: Blueprint neu importieren / Automation neu laden**

In HA: *Einstellungen → Automationen & Szenen → Blueprints → Blueprint neu laden*
(oder die betroffene Automation einmal speichern, damit die neuen Inputs erscheinen).

- [ ] **Step 2: Neue Helfer aus `examples/akkusteuerung_helpers.example.yaml` anlegen**

Per Copy-Paste in `configuration.yaml`/Package, HA neu starten. Prüfen, dass
`input_text.akkusteuerung_modbus_letzter_schreibwert` und
`input_datetime.akkusteuerung_modbus_letzter_schreibzeitpunkt` existieren.

- [ ] **Step 3: Erstlauf prüfen (leerer Snapshot)**

Modus auf "Akku Automatisch" setzen, Automation auslösen. Im Log/Logbook prüfen,
dass alle 6 Register geschrieben werden (40151 + 5 Wertregister) — Snapshot war
leer, also `write_needed = true`.

- [ ] **Step 4: Skip-Verhalten prüfen**

Automation erneut auslösen (z. B. `/4`-Min-Tick abwarten oder manuell triggern),
ohne dass sich ein überwachter Wert geändert hat. Im Log prüfen: 40151 wird
geschrieben, die 5 Wertregister NICHT (keine `modbus.write_register`-Logeinträge
für 40793/40795/40797/40799/40801).

- [ ] **Step 5: Änderungs-Trigger prüfen**

`input_number.akkusteuerung_min_ladestaerke` (oder einen anderen überwachten Wert)
ändern. Prüfen, dass die 5 Wertregister diesmal geschrieben werden und beide
Helfer (`input_text`/`input_datetime`) aktualisierte Werte zeigen.

- [ ] **Step 6: Keepalive-Verhalten prüfen**

`keepalive_seconds` testweise auf `30` setzen, warten, ohne Wertänderung erneut
triggern (z. B. manuell die Automation ausführen). Prüfen, dass nach Ablauf der
30s erneut geschrieben wird, obwohl sich nichts geändert hat. Danach wieder auf
sinnvollen Wert (z. B. 180) zurücksetzen.

- [ ] **Step 7: Modus-Wechsel schnell-Laden → Automatisch prüfen**

Modus auf "Akku schnell Laden" setzen (schreibt 40151→802, 40149), dann zurück auf
"Akku Automatisch". Prüfen, dass 40151 zuverlässig auf 803 zurückgesetzt wird —
unabhängig davon, ob die 5 Wertregister sich geändert haben oder nicht. Zusätzlich
(Fix aus Task 6): nach der Rückkehr im Log prüfen, dass die 5 BMS-Wertregister
tatsächlich neu geschrieben werden (Snapshot wurde beim Verlassen von "schnell
Laden" invalidiert) — nicht nur 40151.

- [ ] **Step 8: HA-Neustart-Verhalten prüfen**

HA neu starten. Prüfen, dass beim Start-Trigger immer geschrieben wird (alle 6
Register im Log), unabhängig vom Keepalive-Zustand der Helfer.

- [ ] **Step 8b: Keepalive-Obergrenze über zwei `/4`-Ticks hinweg prüfen (Fix aus Task 6)**

Ein überwachter Wert ändern (Snapshot+Timestamp werden aktualisiert), danach
mindestens 8–10 Minuten lang nichts mehr ändern. Im Log/Logbook prüfen, dass die
tatsächliche Lücke zwischen zwei BMS-Register-Schreibvorgängen (40793–40801) nie
über die `keepalive_seconds`-Einstellung plus ~60s (`/1`-Tick-Intervall) hinausgeht
— insbesondere NICHT bis zum nächsten `/4`-Tick (240s) warten muss. Bestätigt, dass
der neue `/1`-Keepalive-Check tatsächlich greift und nicht durch die Skip-Condition
dauerhaft blockiert wird.

- [ ] **Step 8c: Fehlende Helfer simulieren (Fix aus Task 6)**

Testweise einen der beiden neuen Helfer (`input_text`/`input_datetime`) löschen
oder umbenennen, Automation auslösen. Prüfen: die Modbus-Writes laufen weiterhin
durch (kein Abbruch der Sequenz), im HA-Log erscheint höchstens eine Warnung, aber
kein wiederholter Fehler, der die Automation insgesamt fehlschlagen lässt. Helfer
danach wiederherstellen.

- [ ] **Step 9: Bei Erfolg — push**

Nach erfolgreicher manueller Verifikation: Codex-Pre-Push-Review durchführen
(siehe Memory `codex-precheck-before-push`), dann `git push`.

---

## Self-Review

**Spec-Abdeckung:**
- Scope (nur 5 Wertregister, 40151 immer unconditional) → Task 4. ✓
- State-Storage (2 Helfer + keepalive_seconds, Defaults, max:255, has_date/has_time) → Task 1, Task 5. ✓
- Datenfluss (Variablen, write_needed-Template mit as_timestamp-Guard) → Task 3. ✓
- HA-Start umgeht Gate → Task 2 (Trigger-ID) + Task 3 (`trigger.id == 'ha_start'`). ✓
- Edge Cases (leerer Snapshot, fehlgeschlagener Write, Reihenfolge Timestamp-vor-Snapshot) → Task 4 Step 1 (Reihenfolge), Task 6 Step 3/4 (Live-Verifikation). ✓
- Doku/Versionierung (Beispieldatei, README, CHANGELOG `[1.2.0]`) → Task 5. ✓

**Platzhalter-Scan:** Keine TBD/TODO-Platzhalter; jeder Code-Schritt enthält vollständigen YAML/Jinja-Code.

**Typ-Konsistenz:** Variablennamen (`v_40793`, `v_40795`, `v_40797`, `v_40799`, `current_snapshot`, `write_needed`, `snapshot_helper`, `timestamp_helper`, `keepalive_s`) sind in Task 3 definiert und werden in Task 4 identisch wiederverwendet — keine Abweichungen.
