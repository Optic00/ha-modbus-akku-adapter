# TODO: Härtung SMA-Adapter (Befunde aus den Huawei-Gerätetests 2026-07-11/12)

> **Status 2026-07-12:** Code-Härtung umgesetzt auf Branch `feat/haertung-sperren-semantik`
> (Plan + Adversarial-Review: `docs/superpowers/plans/2026-07-12-haertung-sperren-semantik.md`).
> Die Gerätetests (`docs/geraetetests-haertung-2026-07.md`) sind **Release-Gate** und
> brauchen Bens Go - bis dahin kein Merge nach `main`, kein Deploy.

Quelle: Beim baugleichen Huawei-Adapter (Projekt ha-hesselmann, `ADAPTER-MODUSMATRIX-HUAWEI.md` V2.2) wurden bei Gerätetests vier generische Schwachstellen-Muster gefunden.
Ein Read-only-Review (Opus 4.8, 2026-07-12) hat geprüft, ob dieselben Muster in `blueprints/automation/akku_adapter/sma_stp_se_adapter.yaml` existieren.
Zeilenangaben beziehen sich auf den Stand vom 2026-07-12.

Zentrale Lektion aus der Huawei-Nacht: Der Huawei-Adapter verließ sich für "Pause" auf ein Verbots-Flag (Grid-Charge-Switch).
Der Gerätetest zeigte, dass der Akku in einer aktiven TOU-Ladeperiode mit 5 kW lud, obwohl das Flag aus war.
Nachweislich hart waren nur die 0-W-Leistungsgrenzen (stoppten sogar eine laufende Zwangsentladung).
Sperren dürfen nur auf Mechanismen ruhen, die am Gerät als hart bewiesen sind.

## Befunde

### P1 (kritisch): Sperren-Semantik beruht auf unbewiesenen Verbots-Flags [B4-Teil]

- Pause=OpMod 303, nur Laden=2289, nur Entladen=2290, Dynamisch=1438: reine Modus-Flags, keine 0-W-Grenzen.
- Verschärfend: Der Standardpfad schreibt in den Sperr-Modi das jeweils "verbotene" Fenster mit positivem Wert (in "nur Laden" bleibt 40799/Entladeziel positiv, in "nur Entladen" bleibt 40795/Ladeziel positiv, Z. 433-471). Die Sperre hängt allein am Flag.
- Eigene Code-Kommentare dokumentieren bereits Live-Versagen der OpMod/BatChaMinW-Schiene (WR ignorierte BatChaMinW 5,5 min, dann Volllast-Laden, Z. 336-343; OpMod 2289 mit BatChaMinW==BatChaMaxW führte zu unkontrolliertem Volllast-Laden, Z. 162-174).
- Für 303 und 2290 ist gar kein Gerätetest dokumentiert, für 1438 nur "1 Jahr stabil" per Legacy-Automation.
- [ ] Gerätetest analog Huawei-Pflichttests: Beweisen die Flags 303/2289/2290 wirklich 0-W-Verhalten (SoC + Batterieleistung über mehrere Poll-Zyklen, bei Verbrauch > PV bzw. PV-Überschuss)? → Checkliste `docs/geraetetests-haertung-2026-07.md`, wartet auf Bens Go (Release-Gate).
- [x] Falls SMA harte W-Grenzregister bietet: Sperren zusätzlich oder stattdessen auf 0-W-Grenzen stützen; Fenster (40795/40799) in Sperr-Modi modusabhängig auf 0 schreiben statt unconditional positiv. → Umgesetzt als ZUSÄTZLICHE Verteidigungslinie (`charge_locked`/`discharge_locked`, Fenster [0,0]); am SMA unbewiesen bis Gerätetest. Zusätzlich CmpBMS-Freigabe beim Wechsel Sperr-Modus → Kommando-/Automatik-Modus (Tracker im Schreibwert-Helfer), damit stehengebliebene Sperren die 40149-Schiene nicht blockieren.

### P2 (hoch): Exit-Reihenfolge verletzt Restrict-before-enable [B3]

- Beim Verlassen von Netzladen/schnell Laden in einen Sperr-Modus: erst 40151=803 (unverifiziert), dann unconditional der volle BMS-Fenstersatz mit positiven Zielen, erst danach das Sperr-Register (Z. 422-542).
- [x] Reihenfolge drehen: zuerst Sperrwerte schreiben und verifizieren, dann Modus-Register, erst danach Nennwerte restaurieren. → Geprüft und BEWUSST NICHT gedreht (Adversarial-Review 2026-07-12): mit den P1-Fenstern ist die bestehende Reihenfolge bereits restrict-before-enable. 803 zuerst neutralisiert die evtl. aktive 40149-Ladevorgabe sofort (das ist beim Exit aus Lade-Kommandos die eigentliche Restriktion); die danach geschriebenen Fenster sind in Sperr-Modi restriktiv ([0,0]), OpMod (Enable) kommt zuletzt. Ein 803 am Ende hätte den alten Ladebefehl während der gesamten Schreibsequenz aktiv gelassen. Begründung im Blueprint-Kommentar, Reihenfolge per Strukturtest eingefroren.

### P3 (mittel): Kein Write-Verify [B4-Rest]

- Kein `modbus.write_register` hat Settle/Readback/Retry/Abbruch; alles läuft blind mit festen Delays (2 s bzw. 500 ms).
- [x] Für kritische Writes (Sperr-Register, positive Sollwerte, Rail-Off 40151=803) Readback über die zugehörigen Sensor-Entitäten mit genau 1 Retry und Abbruch+Benachrichtigung bei Abweichung (Muster: Huawei-Blueprint, HSEM). → NICHT 1:1 machbar: die SMA-Schreibregister sind flüchtig und lesen als 0/null zurück (Community-belegt, Registerreferenz "Persistenz"), es gibt keine Readback-Sensoren. Stattdessen Postcondition-Monitoring per Wächter-Blueprint `sma_stp_se_wachter.yaml`: Sperrverletzung (Leistung im Sperr-Modus, 31393/31395), Adapter-Stillstand (Timestamp-Helfer, jetzt in ALLEN Branches gepflegt) und Sensor-blind-Erkennung. Kein Write-Verify im Wortsinn; Grenzen im Blueprint dokumentiert.

### P4 (niedrig): Stille Trigger-Verluste und fehlender Pre-Release-Stale-Check [B1]

- `mode: single` ohne max/max_exceeded (Z. 566): Moduswechsel-Trigger während eines laufenden Laufs werden verworfen.
- Vor freigebenden Writes (z. B. 40149-Setpoint nach 2-s-Delay, Z. 284-294) gibt es keinen erneuten Stale-Check.
- Mitigation vorhanden: jeder Lauf liest den Modus frisch, Reconcile alle 2 min.
- [x] Stale-Check unmittelbar vor jedem freigebenden Write ergänzen; `mode: queued` mit Stale-Recheck erwägen. → Umgesetzt: `mode: queued` (max 3, silent), Stale-Guard als erste Action (HA friert Top-Level-Variablen beim Trigger ein - queued-Läufe mit veralteten Fensterwerten werden komplett verworfen), Stale-Cleanup nach dem 2-s-Delay in allen vier Kommando-Branches (bei Modus-Wechsel wird die 802-Schiene per 803 deaktiviert statt nackt abzubrechen, Review-Finding F4). Nebenbei: 40149-Leistungswerte auf 0..10000 W geklemmt (Review-Befund 2026-07-09).

### P5 (dokumentiert, beobachten): Status-Gate blockiert auch Sperren [B2]

- Das WR-Status-Gate (Z. 240-241) blockiert bei unavailable/unknown die gesamte Automation inklusive der Sperr-Modi.
- Bewusste Design-Entscheidung mit SMA-Keepalive-Timeout als Hardware-Fallback (Z. 45-53, 228-239); der 2-min-Reconcile heilt symmetrisch.
- [ ] Nur prüfen, ob die Sperr-Zweige vom Gate ausgenommen werden können, ohne die Keepalive-Argumentation zu brechen.

## Übergabeprompt für die nächste Session

> Lies `TODO-HAERTUNG-SMA-ADAPTER.md` in `~/Dev/Repositorys/ha-modbus-akku-adapter` und arbeite die Punkte P1-P4 am Blueprint `blueprints/automation/akku_adapter/sma_stp_se_adapter.yaml` ab (P1/P2 zuerst; P1-Gerätetests nur nach meinem Go, das ist meine eigene HA-Instanz 192.168.10.2).
> Kontext und Referenzmuster: Huawei-Adapter `~/Dev/sandbox/ha-hesselmann/blueprints/huawei_sun2000_adapter.yaml` (Write-Verify, Restrict-before-enable, Tracker) plus `ADAPTER-MODUSMATRIX-HUAWEI.md` V2.2 (Gerätebefunde G1-G4).
> Hole vor der Umsetzung eine adversariale Zweitmeinung zum Änderungsplan über Codex ein: `/codex:adversarial-review` mit `--model gpt-5.6-sol --effort high`, Fokus: Sperren-Semantik (Verbots-Flags vs. 0-W-Grenzen), Exit-Reihenfolge, Write-Verify-Abdeckung.
> Nach der Umsetzung `/codex:review` (gleiches Modell/Effort) über den Diff laufen lassen, Findings abarbeiten und alles im CHANGELOG-freien Arbeitslog des Repos dokumentieren (CHANGELOG.md nicht manuell anfassen).
