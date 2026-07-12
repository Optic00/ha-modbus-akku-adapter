# Gerätetests Härtung 2026-07 (Release-Gate, nur nach Bens Go)

Anlage: Bens SMA STP SE 10.0 + BYD HVS 12.8 (HA 192.168.10.2).
Beweisziel analog zu den Huawei-Pflichttests: SoC + Batterieleistung (Register 31393/31395) über mehrere Poll-Zyklen beobachten, nicht nur einen Momentanwert.
Diese Tests sind Release-Gate: kein Merge nach `main` und kein Release-Tag, bevor die Sperr-Tests bestanden sind (Adversarial-Review-Finding F1, 2026-07-12).

## Sperr-Semantik (P1-Beweisführung)

- [ ] Pause-Sperre bei Verbrauch > PV: Modus "Akku Pause", Entladeleistung bleibt 0 W über >= 10 min, SoC stabil.
- [ ] Pause-Sperre bei PV-Überschuss: Modus "Akku Pause", Ladeleistung bleibt 0 W über >= 10 min.
- [ ] Entlade-Sperre: "Akku nur Laden" bei Verbrauch > PV: keine Entladung über >= 10 min.
- [ ] Lade-Sperre: "Akku nur Entladen" bei PV-Überschuss: keine Ladung über >= 10 min.

## Handoff Sperr-Modus → Schiene (F2-Validierung)

- [ ] Übergang "Akku Pause" → "Akku schnell Laden": startet das Kommando-Laden binnen weniger Poll-Zyklen (CmpBMS-Freigabe wirkt)?
  Falls verzögert oder blockiert: Freigabe-Set (Fenster offen + OpMod 1438) am Gerät nachjustieren.
- [ ] Übergang "Akku Pause" → "Akku Automatisch": WR kehrt in Eigenregelung zurück, kein Lade-/Entlade-Spike (vgl. v1.3.0-Spike-Mechanismus).
- [ ] Übergang "Akku schnell Laden" → "Akku Pause": Ladeleistung fällt binnen eines Poll-Zyklus auf 0 (803 zuerst, dann [0,0]-Fenster, dann OpMod 303).

## Wächter (P3-Probe)

- [ ] Sperrverletzungs-Probe: Wächter-Schwelle testweise auf 20 W, Modus Pause bei anliegender Last, Adapter-Automation kurz deaktivieren, bis der WR-Timeout die Sperre löst: Benachrichtigung kommt.
  Danach Schwelle zurück auf 100 W und Adapter wieder aktivieren.
- [ ] Stillstands-Probe: Adapter-Automation 7 min deaktivieren: Stillstands-Meldung kommt; Automation wieder aktivieren, Meldung wiederholt sich nicht grundlos.
- [ ] Blind-Probe: einen der beiden Leistungssensoren testweise unavailable machen (z. B. Modbus-Sensor umbenennen/deaktivieren): "Wächter blind"-Meldung nach ~5 min.

## Regression (bestehende Adapter-Checkliste)

- [ ] Pause / schnell Laden / schnell Entladen / Dynamisch-Übergang live durchtesten (wie vor jedem Release).
- [ ] Dynamisch-Settling: nach Wechsel in Dynamisch bleibt die Ladeleistung im 330-s-Fenster <= ~625 W.
- [ ] Kein falscher Stillstandsalarm nach > 6 min in "Akku schnell Laden" (Timestamp-Pflege in Kommando-Branches).

## Befunde

(Nach den Tests hier eintragen: Datum, Modus, Recorder-Auszug, Bewertung.)
