# Gerätetests Härtung 2026-07 (Release-Gate)

Anlage: SMA STP SE 10.0 + BYD HVS 12.8.
Beweisziel analog zu den Huawei-Pflichttests: SoC + Batterieleistung (Register 31393/31395) über mehrere Poll-Zyklen beobachten, nicht nur einen Momentanwert.
Beweissprache (Codex-Review 12.7.): der Recorder liefert 5-s-Samples; "0 W" heißt daher immer "alle aufgezeichneten 5-s-Samples waren 0 W", Transienten unterhalb der Poll-Auflösung sind damit nicht ausgeschlossen (Befund B1 zeigt genau so einen Fall).
Für Übergangs-Feinmessungen (B1-Follow-up) ist eine 1-s-Auflösung nötig.
Diese Tests sind Release-Gate: kein Merge nach `main` und kein Release-Tag, bevor die Sperr-Tests bestanden sind (Adversarial-Review-Finding F1, 2026-07-12).

Testlauf 1: 2026-07-12 vormittags (Deploy 10:12, PV-Überschuss 5-10 kW), Recorder-verifiziert.
Offen bleiben die Verbrauch-über-PV-Fälle (abends nachholen), die Blind-Probe und die EV-/Regressionsfälle mit Auto.

## Sperr-Semantik (P1-Beweisführung)

- [ ] Pause-Sperre bei Verbrauch > PV: Modus "Akku Pause", Entladeleistung bleibt 0 W über >= 10 min, SoC stabil. (OFFEN: Abendblock Teil 2, ~21:00)
- [x] Pause-Sperre bei PV-Überschuss: BESTANDEN 2026-07-12 10:32-10:44. Fenster [0,0]/[0,0] + OpMod 303, Lade- UND Entladeleistung in allen 5-s-Samples 0 W, SoC konstant 54,4 %, Export 9-10 kW.
- [ ] Entlade-Sperre: "Akku nur Laden" bei Verbrauch > PV: keine Entladung über >= 10 min. (OFFEN: Abendblock Teil 2, ~21:00)
- [x] Lade-Sperre: "Akku nur Entladen" bei PV-Überschuss: BESTANDEN 2026-07-12 10:16-10:26+. Fenster [0,0] Laden / [0,5052] Entladen + OpMod 2290, Ladeleistung in allen 5-s-Samples 0 W bei 5-9,5 kW Export, SoC konstant.

## Handoff Sperr-Modus → Schiene (F2-Validierung)

- [x] Übergang "Akku Pause" → "Akku schnell Laden": BESTANDEN 2026-07-12 10:45. Kommando-Laden startet ~15 s nach Umschaltung punktgenau auf dem 2000-W-Sollwert (2033 W um 10:45:40). Keine 300-s-Blockade; CmpBMS-Freigabe wirkt.
- [x] Übergang "Akku Pause" → "Akku Automatisch": BESTANDEN 2026-07-12 10:48. WR in Eigenregelung, lädt den vollen Überschuss (~10,4 kW, erwartetes Automatisch-Verhalten), keine Anomalie. Bekannte 5-s-Null-Blips exakt im 2-min-Raster = 802/803-Keepalive des Automatik-Branches (Bestandsverhalten).
- [x] Übergang "Akku schnell Laden" → "Akku Pause": BESTANDEN MIT BEFUND 2026-07-12 10:47. Ladeleistung fällt binnen zweier Poll-Samples von 2038 W auf 0. Dazwischen genau EIN 5-s-Sample mit 9661 W: im Fenster zwischen 40151=803 (Schiene frei) und dem Landen der [0,0]-Fenster regelt der WR ~1-3 s intern und griff bei 10 kW Überschuss kurz voll zu. Siehe Befund B1 unten.

## Wächter (P3-Probe)

- [x] Sperrverletzungs-Probe: BESTANDEN 2026-07-12 11:10:42 (realistische Provokation statt Schwellen-Trick: Adapter aus, Register liefen aus, WR lud intern 8,8 kW im Modus Pause). Template-Trigger feuerte nach exakt 3 min durchgehender Ladung; persistente Meldung + Push (mobile_app_iphone_15_ben) mit korrekten Werten (8811 W, Schwelle 100 W).
- [x] Stillstands-Probe: BESTANDEN 2026-07-12 11:10:00 (Tick). Adapter 10:59 deaktiviert, Meldung beim ersten Tick mit Alter > 6 min (484 s beim Folgelauf). Nach Reaktivierung 11:12 keine grundlose Wiederholung (persistent_notification mit fester notification_id überschreibt sich zudem selbst).
- [x] Blind-Probe: BESTANDEN 2026-07-12 18:39:33 (realistische Simulation: SMA-Integration des Hybrid-WR 6,5 min deaktiviert, alle Sensoren unavailable). "Wächter blind"-Meldung exakt nach der 5-min-for:-Frist; Duplikat-Trigger des zweiten Sensors von mode: single korrekt verschluckt. Recovery nach Re-Enable sauber.

## Regression (bestehende Adapter-Checkliste)

- [x] Pause / schnell Laden / Automatisch / Dynamisch-Übergänge live durchgetestet (Testlauf 1). "schnell Entladen": BESTANDEN Abendblock 12.7. 18:08-18:14 (3 Zyklen bei PV-Überschuss, Sollwert punktgenau ~1950 W; Exits nach Pause 2x und nur Laden 1x, je mit 1-3-s-Burst und danach korrektem Zielzustand; "nur Laden" regelte anschließend sauber im dyn. Fenster ~1030 W).
- [x] Dynamisch-Settling: BESTANDEN 2026-07-12 10:57. Nach Strategie-Rückschaltung auf Dynamisch: Snapshot 0|500|0|5052, Ladeleistung 558 W = Settling-Cap 500 W (+ Messtoleranz).
- [x] Kein falscher Stillstandsalarm in Kommando-Modi: strukturell erfüllt (Timestamp-Pflege in allen Branches, Strukturtest); Langzeit-Fall > 6 min in "schnell Laden" implizit über den Betrieb weiter beobachten.

## Abendblock Teil 1 (12.7. 18:05-18:55, 1-Hz-Logger parallel)

- [x] Queue-Sättigung: BESTANDEN 18:14. 5 Modus-Wechsel in 12 s (schnell Entladen → Pause → Dynamisch → Pause → Dynamisch → Pause); Endzustand konvergierte auf korrektes Pause-Sperrset, keine "Already running"/max_exceeded-Warnungen.
- [x] Status-Gate-Provokation: BESTANDEN 18:19-18:28 (inverter_ok_states temporär auf Dummy-Wert). Gate blockte alle Writes; Register liefen exakt 5:05 min nach letztem Write aus (Timeout damit 2x präzise belegt, vgl. B2); WR lud intern 94→98,4 % und stoppte selbst; Stillstands-Alarm pünktlich beim ersten /5-Tick mit Alter > 6 min (18:25). Verletzungs-Alarm korrekt STILL: interne Ladeepisode dauerte nur 1:55 min (< 3-min-Karenz) - Karenz wirkt wie designed.
- [x] HA-Neustart-Smoke: BESTANDEN 18:46-18:49. Adapter lief sofort per ha_start-Trigger (18:48:00), Registersatz 3 s später geschrieben; Wächter, opti-Schicht und EV-Sensoren sauber zurück; keine Fehlalarme.

**Nebenbefunde Abendblock:**
- Zweiter SoC-Resync des Tages während der Gate-Blockade (WR intern auf 100 %, Zellmax 3,619 V) - zweiter Ladeschluss-Datenpunkt für das Taper/Balancing-Feature (separater PR).
- Stall-Push wiederholt sich bei langem Ausfall alle 5 min (persistent_notification überschreibt sich, der Mobile-Push nicht) - vertretbar, Politur-Kandidat (Rate-Limit).
- Manuell deaktivierte Automationen überleben den HA-Neustart nicht (Strategie kam automatisch wieder an - Restart-Durability wirkt in die sichere Richtung, aber bei Tests einplanen).
- Exit-Burst (B1) auch in Gegenrichtung reproduziert: Exits aus schnell Entladen zeigen 1-2-s-Burst in LADErichtung (6,8-7,2 kW bei PV-Überschuss) - der WR greift in der Übernahmelücke, was die interne Regelung will. Insgesamt 4x reproduziert.

## Befunde

**B1 - Exit-Burst schnell Laden → Pause: mit 1-s-Auflösung vermessen und als geräteinhärent eingestuft (2026-07-12 mittags, Messlog `messdaten-b1-praearm-20260712.log`):**
Messaufbau: unabhängiger 1-Hz-Modbus-Logger (pymodbus, read-only auf 31393/31395), zwei normale Adapter-Exits schnell Laden (2 kW) → Pause bei ~10 kW PV-Überschuss.
Reproduzierbares Muster in beiden Zyklen: nach dem Pause-Befehl läuft die 2-kW-Ladung noch ~10-13 s weiter (obwohl der komplette Pause-Satz nach ~4 s geschrieben ist), dann 2-3 s Burst auf ~10,7 kW (interne Regelung), dann hart 0 W.
Energie pro Exit: ~0,006-0,009 kWh - vernachlässigbar.
Einstufung: WR-interne Übernahmelatenz, KEIN Reihenfolge-Problem des Adapters; die Sperre greift zuverlässig, nur eben ~13-16 s nach dem Befehl.

**B4 - Pre-Arm-Variante (Fenster/OpMod VOR 803) am Gerät DURCHGEFALLEN (2026-07-12 12:07-12:11):**
Test: bei aktiver 802-Schiene (2 kW Laden) manuell kompletten CmpBMS-Satz [0,0]×4 + GridWSpt 0 + OpMod 303 geschrieben, je 500 ms Abstand.
Ergebnis 1: die Schiene gewinnt - Laden lief unverändert mit ~2,06 kW weiter (Writes stören das Kommando nicht).
Ergebnis 2 (entscheidend): nach dem anschließenden 803 sperrte der WR NICHT, sondern ging in dauerhafte interne Volllast (~10,7 kW, > 45 s, bis der Adapter den Satz nach 803 erneut schrieb).
Die bei aktiver Schiene geschriebenen CmpBMS-Werte werden also verworfen, nicht armiert.
Konsequenz: der Follow-up-Kandidat "Fenster vor 803" ist tot; die bestehende Reihenfolge (803 zuerst, dann Fenster+OpMod) ist die einzig funktionierende der beiden Varianten und bleibt.
Der 2-3-s-Burst (B1) ist der geräteinhärente Preis dieser Mechanik und mit dem 2-min-Reconcile als Rückfallnetz akzeptiert; ein Abbruch der Schreibsequenz nach 803 verlängert die interne Phase bis zum Reconcile (bekanntes, dokumentiertes Restrisiko).

**B2 - Register-Timeout-Timing:** Nach Adapter-Stopp 10:59 begann das interne Volllast-Laden ca. 11:04-11:07 (Sperrverletzungs-Trigger 11:10:42 minus 3 min for:-Fenster), also ~5-8 min nach dem letzten Schreibzyklus.
Konsistent mit dem dokumentierten ~5-min-Rückfall der externen Steuerung bzw. der 300-s-Erneuerungspflicht.

**B3 - Wächter-Timing wie ausgelegt:** Verletzung nach exakt 3 min Dauer (Template-for:), Stillstand beim ersten /5-Tick nach Überschreiten der 6-min-Schwelle.
