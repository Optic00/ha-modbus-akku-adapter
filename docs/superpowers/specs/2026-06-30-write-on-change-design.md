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
- **`keepalive_seconds` Fehlkonfiguration:** Selector-Max von 200 (siehe Nachtrag
  unten — ursprünglich 280, nach finalem Review wegen Tick-Granularität gesenkt)
  verhindert Werte, die in Kombination mit dem `/1`-Keepalive-Tick über das
  300s-Hersteller-Limit hinaus könnten.

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

## Nachtrag (2026-06-30): Fixes aus dem finalen Whole-Branch-Review

Der finale Review nach Implementierung der Tasks 1–5 fand drei Probleme, von zwei
unabhängigen Gegenchecks (Opus-Subagent + Codex) bestätigt:

**1. Critical — Keepalive-Garantie durch Tick-Granularität ausgehebelt.** Der
`write_needed`-Gate wird nur bei Trigger-Feuern neu evaluiert. Einziger periodischer
Wecker bei stabilen Werten war der bestehende `/4`-Minuten-Tick (240s). Die
tatsächliche Schreib-Lücke kann dadurch auf `keepalive_s + 240s` anwachsen (bei
Default 180s → bis ~420s, bei dem ursprünglichen Selector-Max 280s → bis ~520s) —
über dem 300s-Hersteller-Limit. Der alte Code (vor Write-on-Change) schrieb bei
jedem 240s-Tick unconditional und garantierte damit eine Obergrenze von 240s; das
neue Feature konnte diese Sicherheitseigenschaft verletzen.

**Fix:** Ein zusätzlicher, feinerer periodischer Trigger `minutes: /1` mit
`id: keepalive_check` wird ergänzt (der bestehende `/4`-Tick bleibt zusätzlich
bestehen, da Register 40151 außerhalb des Gates seinen eigenen Keepalive über diesen
Tick braucht). Eine neue Skip-Condition im `conditions:`-Block
(`{{ not (trigger.id == 'keepalive_check' and not write_needed) }}`) sorgt dafür,
dass ein `/1`-Tick, bei dem nichts fällig ist, den **gesamten** Automation-Lauf
abbricht, bevor überhaupt 40151 geschrieben wird — dadurch bleibt die Modbus-Last
niedrig, obwohl der Tick häufiger feuert. `keepalive_seconds`-Selector-Max wird von
280 auf 200 gesenkt: Worst-Case-Lücke `200 + 60 = 260s`, plus ~6s Schreibsequenz ≈
266s, mit ausreichend Marge unter dem 300s-Limit.

**2. Important — BMS-Wertregister werden nach einem "schnell Laden/Entladen"-Ausflug
nicht zwangsweise neu geschrieben.** Dieselbe Problemklasse wie der ursprünglich für
40151 gefundene Bug (Scope-Abschnitt oben), aber nie auf die fünf Wertregister
angewendet: Diese Branches schreiben nur 40151/40149 und `stop:`en, ohne die
BMS-Wertregister zu berühren. Kehrt man zu einem Standardpfad-Modus zurück und der
Snapshot ist zufällig identisch zum letzten gespeicherten UND der Keepalive ist noch
nicht abgelaufen, werden die Wertregister nicht neu geschrieben — obwohl unklar ist,
ob der WR sie während der 802-Phase intern verwirft (unverifizierte
Hardware-Annahme, daher Important statt Critical).

**Fix:** In beiden Branches wird vor `stop:` der Snapshot-Helfer geleert
(`input_text.set_value` mit `value: ""`), was beim nächsten Standardpfad-Lauf einen
garantierten Snapshot-Mismatch und damit einen Rewrite erzwingt — spätestens beim
nächsten `/1`-Tick (&lt;60s später).

**3. Important — Fehler-Spam bei fehlenden Helfern auf unmigrierten Systemen.** Die
CHANGELOG-Doku verspricht einen sauberen Fallback für Nutzer, die die neuen Helfer
noch nicht angelegt haben; die `input_datetime.set_datetime`/`input_text.set_value`-
Aufrufe zielen aber auf nicht existierende Entities, was zu wiederholten
Fehlermeldungen führen kann.

**Fix:** Alle Helfer-Update-Aktionen (im Standardpfad-Gate sowie die neue
Snapshot-Invalidierung in Fix 2) bekommen `continue_on_error: true` — verhindert,
dass ein fehlender Helfer die Sequenz abbricht oder Fehler eskaliert. Fail-safe-
Richtung: schlägt das Update fehl, bleibt der alte Timestamp/Snapshot stehen →
`write_needed` bleibt eher `true` → tendenziell mehr statt weniger Writes.

## Nachtrag 2 (2026-06-30): Fix für eine von Fix 1 verursachte Nebenwirkung

Die erneute finale Review (nach Nachtrag 1) fand, dass Fix 1 selbst eine neue
Nebenwirkung hat, ebenfalls von Opus-Subagent und Codex bestätigt:

**Important — `/1`-Tick überspringt nie in „Akku Automatisch"/„schnell
Laden"/„schnell Entladen".** `write_needed` wird ausschließlich im
Standardpfad-Gate berechnet bzw. der zugehörige Timestamp-Helfer dort
aktualisiert. Die drei genannten Modi `stop:`en aber VOR dem Standardpfad und
aktualisieren den Timestamp nie — dort ist `write_needed` deshalb dauerhaft
`true`. Der `/1`-Tick übersprang den Lauf in diesen Modi folglich nie: die
Automation lief dort alle 60s statt wie zuvor alle 240s (über den unveränderten
`/4`-Tick) — eine 4-fache Lasterhöhung im Default-Modus „Automatisch", obwohl das
Feature genau das Gegenteil bezweckt. Betrifft auch unmigrierte v1.1.0-Systeme
ohne die neuen Helfer (dort ist `write_needed` ebenfalls überall dauerhaft
`true`).

**Fix:** Eine neue Variable `early_stop_modes` (Liste der drei Modus-Strings) und
`mode_select_entity` (für Jinja-Zugriff auf den Modus, analog zu
`dyn_charge_entity`) werden ergänzt. Die Skip-Condition wird erweitert (positive
Formulierung, von Codex empfohlen):

```yaml
  - condition: template
    value_template: >-
      {{ trigger.id != 'keepalive_check'
         or (states(mode_select_entity) not in early_stop_modes and write_needed) }}
```

Der `/1`-Tick überspringt jetzt zusätzlich, sobald der aktuelle Modus einer der
drei early-stop-Modi ist — unabhängig von `write_needed`, da der `/1`-Tick dort
ohnehin keinen Zweck hat (diese Modi nutzen den BMS-Gate nie). Der bestehende
`/4`-Tick bleibt unverändert und übernimmt für diese drei Modi weiterhin die
periodische Auffrischung, exakt wie vor dem gesamten Write-on-Change-Feature.
