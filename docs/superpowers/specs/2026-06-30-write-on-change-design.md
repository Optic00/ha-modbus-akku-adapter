# Write-on-Change für `sma_stp_se_adapter.yaml`

Status: genehmigt (Brainstorming abgeschlossen 2026-06-30)

## Problem

Der "Standardpfad"-Block des Adapters (`blueprints/automation/akku_adapter/sma_stp_se_adapter.yaml`,
Zeilen 182–243) schreibt bei **jedem** Trigger — State-Change einer von ~8 überwachten
Entities, der `/4`-Minuten-Tick oder HA-Start — sechs Modbus-Register nacheinander mit
je 1s Delay: 40151, 40793, 40795, 40797, 40799, 40801. Das passiert auch dann, wenn
sich nur ein einziger überwachter Wert geändert hat: ~6s unnötige Modbus-Last pro
Trigger.

Laut `docs/modbus-register-referenz.md` müssen nur die BMS-Limit-Register
40793–40801 "zyklisch max. alle 300 s" geschrieben werden, sonst läuft die
SMA-Fremdsteuerung aus (Keepalive-Zwang). Für 40151 sowie die mode-spezifischen
Register (40149, 41259, 40236) gibt es keinen dokumentierten Keepalive-Zwang.

## Scope

Write-on-Change gilt **nur** für die fünf Wertregister des Standardpfad-Blocks:
40793, 40795, 40797, 40799, 40801. Mode-spezifische Register (40149, 41259, 40236)
bleiben unverändert (unconditional, aber ohnehin selten getriggert — Risiko eines
undokumentierten Re-Write-Bedarfs überwiegt den marginalen Lastgewinn).

Register **40151 wird weiterhin immer unconditional geschrieben**, am Anfang des
Standardpfads, außerhalb des Write-on-Change-Gates. Begründung: Die Branches
"Akku schnell Laden"/"Akku schnell Entladen" setzen 40151 auf `802` und beenden die
Automation per `stop:`, ohne den Standardpfad zu durchlaufen — nur ein unconditionales
40151-Schreiben am Standardpfad-Anfang garantiert zuverlässig den Rücksprung auf `803`
("Normalbetrieb"), unabhängig vom Snapshot-Zustand der Wertregister. Eine Alternative
(Snapshot-Invalidierung in den schnell-Branches) wurde verworfen — sie koppelt die
Korrektheit eines Steuer-Gate-Registers unnötig an einen Optimierungs-Cache.

## State-Storage

Zwei neue Blueprint-Inputs (Entity-Selektoren, konsistent mit dem bestehenden
Adapter-Stil — z.B. `battery_capacity_sensor`):

- `last_write_value_helper` — Domain `input_text`, Default
  `input_text.akkusteuerung_modbus_letzter_schreibwert` (`max: 255`).
  Speichert einen Snapshot der zuletzt geschriebenen Werte der 5 Wertregister als
  Pipe-getrennten String (z.B. `0|2560|0|5000|0`).
- `last_write_time_helper` — Domain `input_datetime`, Default
  `input_datetime.akkusteuerung_modbus_letzter_schreibzeitpunkt`
  (muss `has_date: true` und `has_time: true` haben). Zeitpunkt des letzten
  tatsächlichen Schreibvorgangs der 5 Wertregister — wird bei **jedem** Schreiben
  aktualisiert, auch reinen Keepalive-Writes ohne Wertänderung.
- `keepalive_seconds` — `number`-Selector direkt im Blueprint (kein Helfer nötig,
  reiner Konfigwert), Default `180`, `min`/`max: 280` (Sicherheitsmarge unter dem
  300s-Hersteller-Limit), `step`, Einheit Sekunden.

Beide Helfer werden zusätzlich in `examples/akkusteuerung_helpers.example.yaml`
ergänzt, damit Nutzer sie per Copy-Paste statt manuellem GUI-Anlegen bekommen.

Beide Inputs bekommen Defaults (Pflicht für Abwärtskompatibilität): bestehende
v1.1.0-Importe dürfen beim Update nicht brechen. Fehlt/​ist ein Helfer
`unknown`/leer, wird das wie "Keepalive abgelaufen" behandelt → es wird geschrieben
(sicherer Fallback, kein Hard-Error).

## Datenfluss

```
variables:
  snapshot_helper: !input last_write_value_helper
  timestamp_helper: !input last_write_time_helper
  keepalive_s: !input keepalive_seconds
  v_40793: <berechneter Wert, wie bisher: min(min_ladestaerke, dyn_charge)>
  v_40795: <dyn_charge>
  v_40797: <berechneter Wert, wie bisher: min(min_entladestaerke, max_entladestaerke)>
  v_40799: <max_entladestaerke>
  current_snapshot: "{{ [v_40793, v_40795, v_40797, v_40799, 0] | join('|') }}"
  write_needed: >-
    {% set valid_dt = state_attr(timestamp_helper, 'has_date') and state_attr(timestamp_helper, 'has_time') %}
    {% set last_ts = as_timestamp(states(timestamp_helper), none) if valid_dt else none %}
    {{ current_snapshot != states(snapshot_helper)
       or last_ts is none
       or (now().timestamp() - last_ts) > (keepalive_s | int(0)) }}
```

Ablauf im Standardpfad:

1. `40151 → [0, 803]` schreiben (unconditional, wie bisher).
2. `if: write_needed` → `then`: 40793, 40795, 40797, 40799, 40801 schreiben
   (Reihenfolge/Delays wie bisher), danach **erst** `input_datetime.set_datetime`
   (Timestamp), **dann** `input_text.set_value` (Snapshot) — diese Reihenfolge macht
   den Snapshot zur "committed"-Marke: bricht die Schreibsequenz vorzeitig ab, bleibt
   der alte Snapshot stehen und der nächste Trigger erzwingt automatisch einen Retry.

**Ausnahme HA-Start:** Der `homeassistant: start`-Trigger umgeht das Gate bewusst —
bei HA-Start wird immer geschrieben (`write_needed` wird für diesen Trigger-Fall fest
auf `true` gesetzt, z.B. über `trigger.platform == 'homeassistant'`). Begründung: Nach
einem Neustart ist der tatsächliche Zustand des WR/BMS unbekannt; der restaurierte
Snapshot beschreibt nur, was HA *glaubt* zuletzt geschrieben zu haben, nicht was das
Gerät aktuell hält. Das entspricht der ursprünglichen Intention des Start-Triggers und
ist rückwärtskompatibel zum bisherigen Verhalten.

`mode: single` bleibt unverändert (nicht `restart`/`queued`) — verhindert, dass ein
parallel laufender Schreibvorgang abgebrochen wird, während Snapshot/Timestamp
aktualisiert werden.

## Edge Cases

- **Erstinstallation / neue Helfer:** Snapshot leer → `write_needed = true` → erster
  Lauf schreibt immer.
- **HA-Neustart:** Helfer überleben (HA restored state), aber der Start-Trigger
  schreibt ohnehin immer (s.o.) — kein Verhaltensunterschied zu heute.
- **Fehlgeschlagener Modbus-Write:** Snapshot bleibt alt (s. Reihenfolge oben) →
  nächster Trigger erzwingt Retry.
- **`input_datetime` ungültig/falsch konfiguriert (nur Zeit, kein Datum):**
  `has_date`/`has_time`-Guard fängt das ab → behandelt wie "Keepalive abgelaufen".
- **`keepalive_seconds` Fehlkonfiguration:** Selector-Max von 280 verhindert Werte
  über dem 300s-Hersteller-Limit.

## Doku & Versionierung

- `examples/akkusteuerung_helpers.example.yaml`: zwei neue Helfer ergänzen.
- `README.md`: neue Helfer als "ab v1.2.0 benötigt" dokumentieren.
- `CHANGELOG.md`: Eintrag aus "Geplant" (Unreleased) entfernen, neuer Abschnitt
  `[1.2.0]` — additives MINOR-Release (alle neuen Inputs haben Defaults, analog zum
  v1.1.0-Präzedenzfall). Geänderten HA-Start-Charakter (jetzt explizit
  Gate-umgehend) unter "Geändert" vermerken, auch wenn das Verhalten gegenüber heute
  unverändert bleibt.
- Kein CI/Test-Setup im Repo vorhanden. Verifikation: YAML-Syntaxprüfung, danach
  manueller Live-Test am Maintainer-System (Modbus-Last vorher/nachher beobachten,
  Moduswechsel schnell-Laden → Automatisch prüfen, HA-Neustart-Verhalten prüfen).

## Out of Scope

- Mode-spezifische Register (40149, 41259, 40236) — keine Änderung.
- Capability-Schicht, `sma_sbs_adapter.yaml` — andere Roadmap-Punkte, unabhängig.
