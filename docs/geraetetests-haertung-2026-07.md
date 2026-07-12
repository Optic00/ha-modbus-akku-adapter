# Gerätetests Härtung 2026-07 (Release-Gate)

Anlage: SMA STP SE 10.0 + BYD HVS 12.8.
Beweisziel analog zu den Huawei-Pflichttests: SoC + Batterieleistung (Register 31393/31395) über mehrere Poll-Zyklen beobachten, nicht nur einen Momentanwert.
Beweissprache (Codex-Review 12.7.): der Recorder liefert 5-s-Samples; "0 W" heißt daher immer "alle aufgezeichneten 5-s-Samples waren 0 W", Transienten unterhalb der Poll-Auflösung sind damit nicht ausgeschlossen (Befund B1 zeigt genau so einen Fall).
Für Übergangs-Feinmessungen (B1-Follow-up) ist eine 1-s-Auflösung nötig.
Diese Tests sind Release-Gate: kein Merge nach `main` und kein Release-Tag, bevor die Sperr-Tests bestanden sind (Adversarial-Review-Finding F1, 2026-07-12).

Testlauf 1: 2026-07-12 vormittags (Deploy 10:12, PV-Überschuss 5-10 kW), Recorder-verifiziert.
Offen bleiben die Verbrauch-über-PV-Fälle (abends nachholen), die Blind-Probe und die EV-/Regressionsfälle mit Auto.

## Sperr-Semantik (P1-Beweisführung)

- [ ] Pause-Sperre bei Verbrauch > PV: Modus "Akku Pause", Entladeleistung bleibt 0 W über >= 10 min, SoC stabil. (OFFEN: abends)
- [x] Pause-Sperre bei PV-Überschuss: BESTANDEN 2026-07-12 10:32-10:44. Fenster [0,0]/[0,0] + OpMod 303, Lade- UND Entladeleistung in allen 5-s-Samples 0 W, SoC konstant 54,4 %, Export 9-10 kW.
- [ ] Entlade-Sperre: "Akku nur Laden" bei Verbrauch > PV: keine Entladung über >= 10 min. (OFFEN: abends)
- [x] Lade-Sperre: "Akku nur Entladen" bei PV-Überschuss: BESTANDEN 2026-07-12 10:16-10:26+. Fenster [0,0] Laden / [0,5052] Entladen + OpMod 2290, Ladeleistung in allen 5-s-Samples 0 W bei 5-9,5 kW Export, SoC konstant.

## Handoff Sperr-Modus → Schiene (F2-Validierung)

- [x] Übergang "Akku Pause" → "Akku schnell Laden": BESTANDEN 2026-07-12 10:45. Kommando-Laden startet ~15 s nach Umschaltung punktgenau auf dem 2000-W-Sollwert (2033 W um 10:45:40). Keine 300-s-Blockade; CmpBMS-Freigabe wirkt.
- [x] Übergang "Akku Pause" → "Akku Automatisch": BESTANDEN 2026-07-12 10:48. WR in Eigenregelung, lädt den vollen Überschuss (~10,4 kW, erwartetes Automatisch-Verhalten), keine Anomalie. Bekannte 5-s-Null-Blips exakt im 2-min-Raster = 802/803-Keepalive des Automatik-Branches (Bestandsverhalten).
- [x] Übergang "Akku schnell Laden" → "Akku Pause": BESTANDEN MIT BEFUND 2026-07-12 10:47. Ladeleistung fällt binnen zweier Poll-Samples von 2038 W auf 0. Dazwischen genau EIN 5-s-Sample mit 9661 W: im Fenster zwischen 40151=803 (Schiene frei) und dem Landen der [0,0]-Fenster regelt der WR ~1-3 s intern und griff bei 10 kW Überschuss kurz voll zu. Siehe Befund B1 unten.

## Wächter (P3-Probe)

- [x] Sperrverletzungs-Probe: BESTANDEN 2026-07-12 11:10:42 (realistische Provokation statt Schwellen-Trick: Adapter aus, Register liefen aus, WR lud intern 8,8 kW im Modus Pause). Template-Trigger feuerte nach exakt 3 min durchgehender Ladung; persistente Meldung + Push (mobile_app_iphone_15_ben) mit korrekten Werten (8811 W, Schwelle 100 W).
- [x] Stillstands-Probe: BESTANDEN 2026-07-12 11:10:00 (Tick). Adapter 10:59 deaktiviert, Meldung beim ersten Tick mit Alter > 6 min (484 s beim Folgelauf). Nach Reaktivierung 11:12 keine grundlose Wiederholung (persistent_notification mit fester notification_id überschreibt sich zudem selbst).
- [ ] Blind-Probe: einen der beiden Leistungssensoren testweise unavailable machen: "Wächter blind"-Meldung nach ~5 min. (OFFEN)

## Regression (bestehende Adapter-Checkliste)

- [x] Pause / schnell Laden / Automatisch / Dynamisch-Übergänge live durchgetestet (Testlauf 1). "schnell Entladen" (OFFEN: abends bei Verbrauch, zusammen mit den Entlade-Sperr-Tests).
- [x] Dynamisch-Settling: BESTANDEN 2026-07-12 10:57. Nach Strategie-Rückschaltung auf Dynamisch: Snapshot 0|500|0|5052, Ladeleistung 558 W = Settling-Cap 500 W (+ Messtoleranz).
- [x] Kein falscher Stillstandsalarm in Kommando-Modi: strukturell erfüllt (Timestamp-Pflege in allen Branches, Strukturtest); Langzeit-Fall > 6 min in "schnell Laden" implizit über den Betrieb weiter beobachten.

## Befunde

**B1 - Exit-Burst schnell Laden → Pause (2026-07-12 10:47:20):**
Genau ein 5-s-Recorder-Sample mit 9661 W Ladeleistung zwischen 803-Write und Wirksamwerden der [0,0]-Fenster, danach hart 0 W.
Energetische Einordnung (~0,02 kWh, Dauer 1-3 s) ist eine SCHÄTZUNG aus einem einzelnen 5-s-Sample; die physische Dauer wurde nicht gemessen (dafür 1-s-Auflösung nötig).
Mechanik: 803 entlässt den WR für ~1-3 s in die interne Regelung, die bei großem PV-Überschuss sofort voll lädt, bis die Sperr-Fenster geschrieben sind.
Follow-up-Kandidat: für Exits IN Sperr-Modi die Reihenfolge Fenster → OpMod → 803 testen; Voraussetzung ist der Gerätenachweis, dass CmpBMS-Writes bei aktiver 802-Schiene angenommen werden.
Bis dahin bewusst so gelassen (Adversarial-Review-Abwägung F3: die Alternative ließe den alten Ladebefehl während der gesamten Schreibsequenz aktiv).

**B2 - Register-Timeout-Timing:** Nach Adapter-Stopp 10:59 begann das interne Volllast-Laden ca. 11:04-11:07 (Sperrverletzungs-Trigger 11:10:42 minus 3 min for:-Fenster), also ~5-8 min nach dem letzten Schreibzyklus.
Konsistent mit dem dokumentierten ~5-min-Rückfall der externen Steuerung bzw. der 300-s-Erneuerungspflicht.

**B3 - Wächter-Timing wie ausgelegt:** Verletzung nach exakt 3 min Dauer (Template-for:), Stillstand beim ersten /5-Tick nach Überschreiten der 6-min-Schwelle.
