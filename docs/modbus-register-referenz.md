# Modbus Register Referenz – SMA STP SE Hybrid

> ## ⚠️ WICHTIGER HAFTUNGSAUSSCHLUSS
>
> **Diese Dokumentation ist eine inoffizielle, community-erstellte Sammlung und wird in keiner Weise von SMA Solar Technology AG begleitet, geprüft oder supportet.**
>
> Die hier aufgeführten Registeradressen wurden durch eigene Tests, Community-Beiträge und eine inoffizielle Antwort des SMA-Supports ermittelt. Es wird **keine Gewähr** für Korrektheit, Vollständigkeit oder Aktualität übernommen. Angaben können sich mit Firmware-Updates ändern.
>
> **Das direkte Beschreiben von Modbus-Registern kann den Wechselrichter, die Batterie oder die gesamte Anlage beschädigen, Garantieansprüche erlöschen lassen oder zu gefährlichen Betriebszuständen führen.**
>
> **Nutzung ausschließlich auf eigene Gefahr. Der Autor übernimmt keinerlei Haftung für Schäden jeglicher Art.**

---

## Getestete Hardware

| Gerät | Firmware | Status |
|---|---|---|
| SMA STP SE 10.0 (Hybrid) | ab ~3.06.xx | ✅ Getestet |
| BYD HVS / HVM Akku | – | ✅ Getestet |
| SMA SBS 2.5 | – | ✅ Schreib-Register bestätigt (Community) – Lese-Register teilweise bekannt |
| SMA SBS 3.7 / 5.0 / 6.0 | 4.7.x | 🔍 Lese-Register gesucht – [Issue #9](https://github.com/Optic00/ha-opti-akkusteuerung/issues/9) |

---

## Verbindungsparameter

| Parameter | Wert |
|---|---|
| Protokoll | Modbus TCP |
| Port | 502 |
| Slave ID | 3 |
| Byte Order | Big Endian |

---

## Lese-Register (Sensoren)

### SMA STP SE Hybrid

| Adresse | SMA Kanal | Datentyp | Einheit | Faktor | Werte / Hinweis |
|---|---|---|---|---|---|
| 30217 | `Operation.GriSwStt` | U32 | – | 1 | `51` = Geschlossen · `311` = Offen · `16777213` = n/a |
| 30775 | `GridMs.TotW` | S32 | W | 1 | Gesamte AC-Wirkleistung |
| 30843 | `Bat.Vol` | U32 | V | 0.01 | Batteriespannung |
| 30845 | `Bat.ChaStt` | U32 | % | 1 | Batterie-SoC |
| 30847 | `Bat.Diag.ActlBatCha` | U32 | – | 1 | Batterie Ladezustand (Status) |
| 30849 | `Bat.Diag.TmpVal` | S32 | °C | 0.1 | Batterietemperatur |
| 30851 | `Bat.Diag.VolMeas` | U32 | V | 0.01 | Gemessene Batteriespannung |
| 30865 | `Metering.GridMs.TotWIn` | U32 | W | 1 | Netzbezug (Import aus Netz) |
| 30867 | `Metering.GridMs.TotWOut` | U32 | W | 1 | Netzabgabe (Einspeisung ins Netz) |
| 30881 | `Operation.PvGriConn` | U32 | – | 1 | `1779` = Getrennt · `1780` = Öffentl. Netz · `1781` = Inselnetz |
| 30953 | `Coolsys.Cab.TmpVal` | **S32** | °C | 0.1 | WR-Innentemperatur – ohne diesen Sensor startet die Modbus-Integration nicht zuverlässig |
| 31061 | `Bat.ChaCtlComAval` | U32 | – | 1 | `1129` = Ja (Steuerung verfügbar) · `1130` = Nein |
| 31393 | `BatChrg.CurBatCha` | U32 | W | 1 | Aktuelle Ladeistung (Momentanwert) |
| 31395 | `BatDsch.CurBatDsch` | U32 | W | 1 | Aktuelle Entladeleistung (Momentanwert) |
| 33003 | `Operation.RunStt` | U32 | – | 1 | `235` = Netzparallelbetrieb · `1463` = Backup · `1469` = Herunterfahren · `2119` = Abregelung |
| 40187 | `Bat.CapacRtgWh` | U32 | Wh | 1 | Batterie Nennkapazität (z.B. 12800 bei BYD HVS 12.8) |
| 40723 | `BatUsDm.BckDmMin` | U32 | % | 1 | Minimale Breite des Ersatzstrombereichs (RW – persistent, nicht zyklisch schreiben) |
| 41255 | `Inverter.WModCfg.WCtlComCfg.WNomPrc` | S16 | % | 1 | Normierte Wirkleistungsbegrenzung durch Anlagensteuerung (RW) |

---

## Schreib-Register (Steuerung)

> ⚠️ Falsche Werte können den WR in unerwünschte Betriebszustände bringen. Anlage beim ersten Schreibversuch beobachten.
>
> ⚠️ Laut SMA sollten **persistierte Parameter** (RW-Register) nicht dynamisch/zyklisch für die Steuerung verwendet werden, da dies den Flash-Speicher belastet. Die unten aufgeführten Register sind als **WO (Write-Only)** oder temporäre Steuerregister eingestuft und können bedenkenlos zyklisch beschrieben werden.

---

### Aktivierungssequenz

Vor Nutzung von Register 40149 muss diese Sequenz ausgeführt werden:

1. `40151` → `[0, 802]` schreiben (Schreibmodus aktivieren)
2. **1–2 Sekunden warten**
3. Steuerbefehl auf `40149` schreiben
4. `40151` → `[0, 803]` schreiben (Normalbetrieb)

| Adresse | SMA Bezeichnung | Wert | Bedeutung |
|---|---|---|---|
| 40151 | – | `[0, 802]` | Externe Steuerung aktivieren |
| 40151 | – | `[0, 803]` | Externe Steuerung deaktivieren / Normalbetrieb |

> ⏱️ **Timeout (Community-Befund):** Ein Nutzer beobachtete, dass 40151 ohne erneutes Schreiben nach ca. 5 Minuten auf Normalbetrieb zurückfällt, und empfiehlt, spätestens alle 4 Minuten neu zu schreiben (Kumpane, PV-Forum [Thread 206718, S. 4](https://www.photovoltaikforum.com/thread/206718-sma-stp10-0-3se-40-welcher-modbus-register-zum-laden-der-batterie/?pageNo=4), 2023-11-02); der konkrete Wert hängt vermutlich vom konfigurierten Timeout ab (s.u.).
> Der Rückfall-Timeout ist als Geräteparameter "Externe Wirkleistungsvorgabe, Timeout" einstellbar (5 s bis 9 h); nach Ablauf kehrt der WR zur internen Regelung zurück (kohaku, ebd., 2023-11-02).
> Berichtete Firmware-Defaults: 30 min bei FW 3.1.9R, 10 min bei FW 3.2.20R (kohaku, PV-Forum [Thread 194071](https://www.photovoltaikforum.com/thread/194071-tripower-smart-energy-begrenzung-der-ladeleistung-des-speichers-%C3%BCber-modbus/), 2023-04-21).
> Details siehe Abschnitt "Community-Wissen & Quellenlage" unten.

---

### Sollwert Batterieleistung direkt (40149)

Quelle: Offizielle SMA Support-Antwort (via [Photovoltaikforum, ajay123](https://www.photovoltaikforum.com/thread/215473-begrenzen-der-lade-entladeleistung-byd-mit-stp-se/?postID=4033278#post4033278))

> Positive Werte = Entladen, negative Werte = Laden (laut SMA)  
> In der Praxis hat sich die folgende Vorzeichen-Kodierung über zwei 16-Bit-Wörter bewährt:

| Adresse | SMA Bezeichnung | Richtung | Wert | Formel |
|---|---|---|---|---|
| 40149 | – | **Laden** | `[65535, X]` | `X = 65536 − Ladeleistung_W` |
| 40149 | – | **Entladen** | `[0, X]` | `X = Entladeleistung_W` |

Beispiel: 3000 W Laden → `[65535, 62536]`

> ℹ️ **Hinweis zur Laden-Formel:** Die beiden 16-Bit-Wörter werden vom WR als ein vorzeichenbehafteter S32 gelesen (Laden = negativ). Das korrekte Zweierkomplement für −P W ist `[65535, 65536 − P]`. Eine ältere, in der Praxis ebenfalls genutzte Variante `65535 − P` ergibt **−(P+1) W** (1 W zu viel) – für die Steuerung praktisch irrelevant, aber `65536 − P` ist exakt. Der Adapter-Blueprint nutzt aktuell diese `65535 − P`-Variante in allen drei Lade-Branches über diesen Pfad (schnell Laden / Netzladen / 0.2C) und ist so live getestet.

---

### BMS-Leistungsgrenzen (40793–40801)

Quelle: Offizielle SMA Support-Antwort (via [Photovoltaikforum, ajay123](https://www.photovoltaikforum.com/thread/215473-begrenzen-der-lade-entladeleistung-byd-mit-stp-se/?postID=4033278#post4033278))

> ⚠️ **Hinweis:** Die Register 40793, 40797, 40801, 41259 und 40236 tauchen in der offiziellen SMA Modbus-Parameterliste **nicht auf** – sie wurden durch direkten SMA-Support-Kontakt bekannt (ajay123) und sind in der Praxis erprobt. Es handelt sich vermutlich um interne Register die auch der Home Manager verwendet.

Diese Register steuern den dynamischen Betrieb.
Der WR regelt dabei **selbstständig den Netzanschlusspunkt** auf den Sollwert `CmpBMS.GridWSpt`.
Die vier Min-/Max-Register sind dabei **Grenzen des Erlaubnisfensters** für diese WR-eigene Regelung, keine Sollwerte: die tatsächliche Lade-/Entladeleistung wählt der WR selbst innerhalb von `[Min, Max]`.
Typische Nutzung: Min-Register auf `0` lassen und die Max-Register als Deckel setzen, z.B. zur Akkuschonung (`BatChaMaxW = 5000`).
Alle Werte in **Watt**, müssen **zyklisch max. alle 300 s** gesendet werden und **innerhalb von 10 s** gesetzt sein.

| Adresse | SMA Bezeichnung | In offizieller Doku | Bedeutung | Typischer Wert |
|---|---|---|---|---|
| 40793 | `CmpBMS.BatChaMinW` | ❌ | Untergrenze Ladeleistungsfenster | `0` |
| 40795 | `CmpBMS.BatChaMaxW` | ✅ | Obergrenze Ladeleistungsfenster (Deckel) | z.B. `2560` (= 0.2C bei 12.8 kWh) |
| 40797 | `CmpBMS.BatDschMinW` | ❌ | Untergrenze Entladeleistungsfenster | `0` |
| 40799 | `CmpBMS.BatDschMaxW` | ✅ | Obergrenze Entladeleistungsfenster (Deckel) | z.B. `5000` |
| 40801 | `CmpBMS.GridWSpt` | ❌ | Netz-Sollwert | `0` |
| 41259 | `CmpBMS.OpMod` | ❌ | Betriebsmodus | siehe unten |

> 💡 Wenn dieses Register-Set verwendet wird, muss die prognosebasierte Akkusteuerung im SunnyPortal/Home Manager deaktiviert sein – der Home Manager nutzt dieselben Register.

> ⚠️ **Einordnung BatChaMinW/BatChaMaxW (Community-Befunde, Stand 2026-07-03):**
> Belegt ist, dass `BatChaMaxW` im Modus Dynamisch (`CmpBMS.OpMod` 1438) als Deckel wirkt (live verifiziert).
> Ebenfalls belegt ist, dass sich die Register im getesteten Setup `OpMod` 2289 mit `BatChaMinW` = `BatChaMaxW` > 0 NICHT als aktive Ladesteuerung eignen.
> Ob `BatChaMinW` > 0 in anderen Konstellationen ein Mindest-Laden erzwingt, ist unbelegt.
> Details, Abgrenzung belegt vs. Hypothese und Reaktion im Adapter: Abschnitt "Bekannte Probleme & Hinweise" unten.

---

### Betriebsmodi (41259 / CmpBMS.OpMod)

| Adresse | SMA Bezeichnung | Wert | Modus |
|---|---|---|---|
| 41259 | `CmpBMS.OpMod` | `[0, 303]` | **Akku Pause** – kein Laden, kein Entladen |
| 41259 | `CmpBMS.OpMod` | `[0, 1438]` | **Dynamisch** – WR regelt auf GridWSpt |
| 41259 | `CmpBMS.OpMod` | `[0, 2289]` | **Nur Laden** – Entladen gesperrt (`Akku Netzladen` nutzt seit v1.5.0 NICHT diesen Pfad, siehe unten) |
| 41259 | `CmpBMS.OpMod` | `[0, 2290]` | **Nur Entladen** |
| 41259 | `CmpBMS.OpMod` | `[0, 2424]` | **Voreinstellung (Dft)** - nicht von diesem Adapter genutzt; evcc verwendet 2424 als Normal-/Hold-Modus (Community, siehe unten) |

> ℹ️ **Modus-Semantik laut Community (kohaku, PV-Forum [Thread 206718, S. 23](https://www.photovoltaikforum.com/thread/206718-sma-stp10-0-3se-40-welcher-modbus-register-zum-laden-der-batterie/?pageNo=23), 2024-11-16):**
> Vollständige Taglist: 303 (Aus), 308 (Ein), 1438 (Auto), 2289 (BatChaMod), 2290 (BatDschMod), 2424 (Voreinstellung/Dft).
> In 2289 wird **nur geladen, wenn am Netzanschlusspunkt eingespeist wird**; bei Bezug geht die Leistung auf 0 und der Akku in Standby.
> In 2290 wird analog **nur entladen, wenn am Netzanschlusspunkt bezogen wird**.
> Das erklärt, warum 2289 kein Laden aus dem Netz erzwingen kann (siehe v1.5.0-Befund unten).

---

### Dynamisch-Modus (40236)

| Adresse | SMA Bezeichnung | Wert | Bedeutung |
|---|---|---|---|
| 40236 | – | `[0, 1438]` | Dynamischen Modus aktivieren (alternativ zu 41259) |

---

### Geräte-Neustart (40077)

> ⚠️ Nur im Notfall / zu Diagnosezwecken verwenden.

| Adresse | SMA Bezeichnung | Wert | Bedeutung |
|---|---|---|---|
| 40077 | `Sys.DevRstr` | `[0, 1415]` | Geräteneustart auslösen |

---

### Grid Guard Code (43090) – veraltet

> ℹ️ Der Grid Guard Code (GGC) war früher nötig um erweiterte Schreibzugriffe freizuschalten.  
> **Der GGC gilt zunehmend als deprecated** (Aussage von Falko Schmidt, SMA, am 18.03.2025 im PV-Forum [Thread 244594](https://www.photovoltaikforum.com/thread/244594-sma-modbus-welche-register-nutzt-ihr/): "Der GGC wird ab der Version 2.16.4.R nicht mehr notwendig sein.").  
> ⚠️ Die kursierende Versionsangabe „2.16.4.R" entspricht dem **SHM2-Firmware-Schema** – die STP-SE-WR-Firmware nutzt eine andere Nummerierung (3.x). Es ist daher unklar, auf welches Gerät bzw. welche Firmware sich die Deprecation genau bezieht; Angabe mit Vorsicht behandeln.  
> Für die Akkusteuerung über 40149 / 40151 / 40793–40801 war der GGC ohnehin **nie erforderlich**.

| Adresse | Beschreibung | Gerät |
|---|---|---|
| 43090 | SMA Grid Guard Code | STP SE / SHM2 |

---

## SMA Sunny Home Manager 2 (SHM2) – eigene Register

> ⚠️ Die folgenden Register gelten für den **SHM2** als Modbus-Slave (typisch: IP des SHM2, Port 502, Slave 3).  
> Sie sind **nicht identisch** mit den Registern des STP SE Hybrid WR. Wer den WR direkt anspricht, verwendet diese Register **nicht**.

### Verbindungsparameter SHM2

| Parameter | Wert |
|---|---|
| Protokoll | Modbus TCP |
| Port | 502 |
| Slave ID | 3 |
| Firmware (bekannt getestet) | 2.15.7.R · 2.16.4.R |

### SHM2 Lese-Register

| Adresse | Beschreibung | Einheit | Hinweis |
|---|---|---|---|
| 30865 | Netzbezug (Import aus Netz) | W | Summe alle Phasen |
| 30867 | Netzabgabe (Einspeisung ins Netz) | W | Summe alle Phasen |

### SHM2 Schreib-Register

| Adresse | Beschreibung | Einheit | Werte | Hinweis |
|---|---|---|---|---|
| 40016 | Normierte Wirkleistungsbegrenzung (`WMaxLimPct`) | % | 0–100 | 0 = PV-Produktion auf 0 drosseln · 100 = volle Leistung · nur ganzzahlige % |
| 40149 | Batterieladung Sollwert | W | – | Wie STP SE direkt |
| 40151 | Externe Steuerung aktivieren/deaktivieren | – | `[0, 802]` / `[0, 803]` | Wie STP SE direkt |

> 💡 Register 40016 auf dem **SHM2** ist der empfohlene Weg um PV-Produktion bei negativen Strompreisen zu drosseln. Logik: Batterie wird zuerst vollgeladen, erst danach werden die Solarmodule gedrosselt. Ohne SHM2 ist eine vollständige DC-seitige Abschaltung nur mit einem physischen Trennschalter möglich.
>
> 🔧 **Ohne SHM2:** Direkt am WR lässt sich die Wirkleistung über **41255 `WNomPrc`** (normierte Wirkleistungsbegrenzung in %) drosseln – 0 % ≈ keine AC-Abgabe. Damit wird die PV-Produktion AC-seitig begrenzt (bei vollem Akku also faktisch gedrosselt). ⚠️ 41255 ist ein **RW-/persistenter Parameter** – nur **ereignisbasiert** schreiben (z.B. beim Wechsel in/aus dem Negativpreis-Fenster), **nicht zyklisch** (Flash-Verschleiß). Dies ist der wahrscheinlichste Hebel für die geplante „PV-Produktionspause" auf Anlagen ohne SHM2 und entspricht dem Roadmap-Punkt „Wirkleistungsbegrenzung bei negativen Strompreisen (Register 41255)" im Schwesterprojekt [`ha-opti-akkusteuerung`](https://github.com/Optic00/ha-opti-akkusteuerung#roadmap).

---

## SMA SBS (Sunny Boy Storage) – Register

> 🔍 **Teilweise geklärt!** Schreib-Register für SBS 2.5 sind durch Community-Tests identisch mit dem STP SE. Für **SBS 3.7–10** sind die Schreib-Register inzwischen durch ein ioBroker-Projekt belegt (s.u.); die meisten **Lese-Register** dort bleiben aber offen: [Issue #9](https://github.com/Optic00/ha-opti-akkusteuerung/issues/9)

Die offizielle SMA Modbus-Dokumentation für den SBS findet sich unter:  
**https://www.sma.de/produkte/batterie-wechselrichter/sunny-boy-storage-37-50-60** → Downloads → „Parameter und Modbus"

### SBS Schreib-Register – bestätigt identisch mit STP SE

> ✅ **SBS 2.5:** Community-Tests bestätigen dieselben Schreib-Register wie der STP SE Hybrid.  
> ✅ **SBS 3.7–10:** dieselbe Registerfamilie wird im ioBroker-Projekt [Maverick78de/SMA_forecast_charging](https://github.com/Maverick78de/SMA_forecast_charging) produktiv genutzt (Geräte `DevType` 9300–9362, s. Abschnitt unten).

| Adresse | Funktion | STP SE | SBS 2.5 | SBS 3.7–10 |
|---|---|---|---|---|
| 40149 | Batterie-Leistungssollwert (`FedInPwrAtCom`) | ✅ | ✅ | ✅ (Maverick) |
| 40151 | Externe Steuerung (`FedInSpntCom`, 802/803) | ✅ | ✅ | ✅ (Maverick) |
| 40236 | Betriebsmodus (`CmpBMSOpMod`) | ✅ | ✅ | ✅ (Maverick) |
| 40793 | `CmpBMS.BatChaMinW` | ✅ | ✅ | ✅ ¹ (Maverick) |
| 40795 | `CmpBMS.BatChaMaxW` | ✅ | ✅ | ✅ (Maverick) |
| 40797 | `CmpBMS.BatDschMinW` | ✅ | ✅ | ✅ ¹ (Maverick) |
| 40799 | `CmpBMS.BatDschMaxW` | ✅ | ✅ | ✅ (Maverick) |
| 40801 | `CmpBMS.GridWSpt` | ✅ | ✅ | ✅ ² (Maverick) |

> ¹ Min-Leistungsregister (40793/40797) schreibt Maverick nur bei bestimmten Geräten (`DevType` 9324–9326, 9356–9359) und **verzögert** (≈1 s nach den anderen), um eine WR-Überlastung zu vermeiden.  
> ² `GridWSpt` (40801) wird nur bei `DevType ≥ 9300` (SBS-Klasse) geschrieben, ebenfalls verzögert.
>
> ⚠️ **Encoding beachten:** Der ioBroker-Modbus-Adapter schreibt **skalare** Registerwerte (z.B. `CmpBMSOpMod = 2424`, `FedInSpntCom = 803`), während diese HA-Doku teils **Wort-Paare** angibt (z.B. `40236 → [0, 1438]`). Werte sind daher **nicht 1:1** übertragbar. Vor Übernahme an echter HA-Anlage prüfen.
> Der OpMod-Wert `2424` wird in der Community-Taglist als "Voreinstellung (Dft)" bezeichnet (kohaku, PV-Forum Thread 206718 S. 23; evcc nutzt ihn als Normal-/Hold-Modus, siehe Abschnitt "Community-Wissen & Quellenlage"); seine exakte Semantik ist aber nicht abschließend geklärt.

### SBS Lese-Register – bekannte Adressen (SBS 2.5)

| Adresse | Beschreibung |
|---|---|
| 30529 | Status |
| 30843 | Batteriespannung |
| 30845 | Batterie SoC |
| 30847 | Batterie-Ladestatus |
| 30849 | Batterietemperatur |
| 30851 | Gemessene Batteriespannung |
| 30955 | Leistungsdaten |
| 31061 | `Bat.ChaCtlComAval` (Steuerung verfügbar) |
| 31393 | Aktuelle Ladeleistung |
| 31395 | Aktuelle Entladeleistung |
| 31397 | Batterieparameter |
| 31401 | Batterieparameter |
| 33001 | Betriebsstatus |
| 34113 | Berechnungswert |
| 34661 | Effizienz/Performance |
| 34665 | Effizienz/Performance |

### SBS 3.7–10 Lese-Register – aus ioBroker-Projekt Maverick78de (Community, ungeprüft in HA)

> 🔍 Quelle: [`bat_regelung_2.3.4.js`](https://github.com/Maverick78de/SMA_forecast_charging/blob/master/bat_regelung_2.3.4.js) (Zeilen 40–60). Die Adressen sind dort als Modbus-Datapoints mit SMA-Kanalnamen hinterlegt und werden produktiv genutzt – aber **nicht** an einer HA-`modbus:`-Instanz dieses Repos verifiziert. Wie die ajay123-Register als inoffiziell behandeln.

| Adresse | SMA Kanal (lt. Maverick) | Typ | Beschreibung |
|---|---|---|---|
| 30053 | `DevTypeId` | input | Geräte-Typnummer – SBS-Erkennung (s. Tabelle unten) |
| 30775 | `PowerAC` | input | AC-Leistung (auch beim STP SE) |
| 30845 | `BAT_SoC` | input | Batterie-SoC – **identisch zum STP SE** |
| 30853 | `ActiveChargeMode` | input | Aktives Ladeverfahren (nur Sunny Island + Blei relevant) |
| 30867 | `TotWOut` | input | Einspeiseleistung am Netzanschlusspunkt |
| 31007 | `RmgChaTm` | input | Restladezeit Boost-Ladung (nur Blei-Speicher) |
| 31009 | `SelfCsmpDmLim` | input | Unteres Entladelimit Eigenverbrauch (Saison) – Geräte < 9356 |
| 40035 | `BatType` | holding | Batterietyp: `1785` = Lithium, sonst Blei/PB |
| 40073 | `SelfCsmpBatChaSttMin` | holding | Unteres Entladelimit Eigenverbrauch – **SBS 3.7–10** (statt 31009) |
| 40189 | `WMaxCha` | holding | Max. Ladeleistung des BatWR (auslesbar) |
| 40191 | `WMaxDsch` | holding | Max. Entladeleistung des BatWR (auslesbar) |

**Geräte-Typnummern (`DevType`, Register 30053) lt. Maverick:**

| DevType | Klasse | Besonderheit im Schreibpfad |
|---|---|---|
| < 9300 | ältere Geräte (z.B. Sunny Island) | nutzen `ActiveChargeMode` (30853); kein `GridWSpt` |
| ≥ 9300 | SBS-Klasse | zusätzlich `GridWSpt` (40801) schreiben |
| 9324–9326 | SBS (Untergruppe) | zusätzlich Min-Register 40793/40797 (verzögert) |
| 9356–9362 | **SBS 3.7–10** | Entladelimit über 40073 statt 31009; 9356–9359 zusätzlich Min-Register |

### Noch gesuchte SBS-3.7+-Lese-Register (nicht in Mavericks Skript)

| Funktion | STP SE Adresse | SBS 3.7–10 |
|---|---|---|
| Batterie SoC | 30845 | ✅ **30845** (Maverick) |
| WR-Status | 33003 | ❓ |
| WR-Temperatur | 30953 | ❓ (Maverick liest keine Temperatur) |
| Steuerung verfügbar | 31061 | ❓ |
| Ladeistung aktuell | 31393 | ❓ (Maverick berechnet indirekt) |
| Entladeleistung aktuell | 31395 | ❓ |

### Hinweis zur SMA-Namenskonvention

Die offizielle SMA-Serviceanleitung *TOR Erzeuger Typ A 2019* ([Download SMA](https://files.sma.de/downloads/TORErzeuger_TYP_A_2019_Paraeinst-SG-de-13.pdf)) listet den SBS3.7-10 als unterstütztes Gerät und bestätigt, dass der SBS dieselbe SMA-Objektnamen-Konvention verwendet (`Inverter.WModCfg.*`, `Inverter.VArModCfg.*` usw.). Die Modbus-**Adressen** können trotzdem abweichen – das Dokument enthält nur Parameternamen, keine Registeradressen.

---

## Bekannte Probleme & Hinweise

**Werte werden nach ~1–4 Minuten zurückgesetzt:**  
Der SMA Home Manager überschreibt die Modbus-Werte, wenn die prognosebasierte Akkusteuerung im SunnyPortal aktiviert ist. Dort deaktivieren.

**Ladeleistung fällt alle 6 Minuten kurz auf 0:**  
Shadefix zieht periodisch die Steuerung zurück. In den WR-Einstellungen auf 30 Minuten setzen oder deaktivieren.

**Register-Adressen in HA vs. SMA-Dokumentation:**  
SMA nummeriert Register ab 40001 (1-indexed). HA Modbus verwendet die Adresse direkt – die HA-Konfiguration nutzt dieselben Zahlen wie die SMA-Dokumentation.

**Ladeleistungs-Spike (~10,7 kW) nach Moduswechsel „nur Entladen" → „Dynamisch" (behoben in v1.3.0):**  
Live beobachtet und 2x reproduziert (2026-07-01, STP SE 10.0 + BYD HVS 12.8): Nach
längerer Verweildauer (>~15 Min) in einem erzwungenen Modus (`CmpBMS.OpMod` = 2290,
„nur Entladen") lädt der WR beim Rücksprung auf „Dynamisch" für ca. 2:20–2:50 Min mit
nahezu Nennleistung, obwohl der Ziel-Sollwert (`CmpBMS.BatChaMaxW` / 40795) unverändert
und kurz zuvor frisch geschrieben war. Der Spike endet abrupt beim nächsten *echten*
Schreibzyklus der BMS-Leistungsgrenzen (40793–40801) – nicht beim ersten danach, sondern
erst beim übernächsten. Kurze Verweildauer (Sekunden) im Forced-Modus löst den Effekt
nicht aus. Vermutete Ursache: der WR verwirft/driftet die intern gültige Ladeleistungs-
grenze, solange Laden im aktuellen Modus irrelevant ist, und übernimmt den korrekten Wert
erst wieder mit dem nächsten tatsächlichen Schreibvorgang nach Rückkehr in „Dynamisch".
Trat ausschließlich nach Umstellung auf einen Adapter/Strategie-Aufbau auf, der die
BMS-Leistungsgrenzen-Registerfamilie (40793–40801/41259) überhaupt erstmals nutzt – vorher
(reiner 40149/40151-Sollwertpfad) nie beobachtet.

Fix ab v1.3.0 (siehe CHANGELOG):
1. Moduswechsel erzwingt einen sofortigen Rewrite der BMS-Leistungsgrenzen (statt bis
   zum nächsten Write-on-Change/Keepalive-Zyklus zu warten).
2. Defensiver Sicherheits-Deckel (500 W) auf die Ladeleistungsgrenze für die ersten
   ~5:30 Min nach jedem Eintritt in „Dynamisch", danach automatischer Rücksprung auf den
   echten Sollwert.
3. Hygiene: `CmpBMS.OpMod` für „Dynamisch" konsistent über 41259 (Sunspec, wie die
   anderen 3 Modi und wie in der offiziellen SMA-Support-Antwort oben) statt über die
   alternative Adresse 40236 geschrieben.
Live verifiziert (Bens Anlage): mit Fix blieb die Ladeleistung im kritischen Fenster
durchgehend ≤ 625 W (vorher bis 10.748 W), sauberer Übergang auf den echten Sollwert nach
Fensterablauf, kein Spike mehr. Zusätzlicher Regressionstest (Pause + Schnell Laden/
Entladen bei 500/1000/2000 W) unauffällig.

**BatChaMinW/BatChaMaxW sind Fenstergrenzen, keine Sollwerte - und taugen nicht als aktive Ladesteuerung (v1.5.0-Befund, 2026-07-03):**  
Live-Regressionstest am SMA STP SE 10.0 (Daten aus dem HA-Recorder).
Der ursprüngliche Ansatz für "Akku Netzladen" versuchte, den WR über `CmpBMS.OpMod` 2289 ("nur Laden") plus `BatChaMinW` (40793) = `BatChaMaxW` (40795) = volle dynamische Ladeleistung (Fensterbreite 0) zum Laden zu zwingen.
Das funktionierte nicht.

*Belegt (Recorder-verifiziert):*
- Im Modus Dynamisch (`OpMod` 1438) wirkt `BatChaMaxW` als Deckel: mit dem 500-W-Settling-Cap des Adapters blieb die Ladeleistung sauber auf ~500 W begrenzt, und auch im historischen Normalbetrieb (Min = 0, Max = dynamische Ladeleistung) hielt sich der WR an das Fenster (Ausnahme: die dokumentierten Einspeisebegrenzungs-Sonderfälle bei Zählerverlust/Abregelung).
- Im getesteten Setup `OpMod` 2289 + Min = Max = 2560 W lud der WR zunächst 5,5 Minuten mit 0 W (trotz Min > 0).
- Danach kippte er in ungeregeltes Laden mit voller PV-Leistung (6,6-6,7 kW, deutlich über Max), Export fiel auf 0 - in diesem Zustand war auch `BatChaMaxW` wirkungslos.
- Der reine 40149/40151-Sollwertpfad (siehe "Sollwert Batterieleistung direkt" oben, wie im Modus "Akku schnell Laden" genutzt) war im selben Test punktstabil: 9 s nach Umschaltung exakt auf dem Sollwert.

*Einordnung/Hypothesen (ein einzelner Test, keine Firmware-Doku):*
- Die Befunde passen zur Fenster-Semantik oben: Min/Max begrenzen die WR-eigene Regelung, sie kommandieren sie nicht.
- Dass `BatChaMinW` > 0 kein Laden erzwang, spricht dafür, dass Min nur eine Untergrenze für den Fall ist, dass der WR überhaupt lädt, und keinen Netzbezug erzwingt - für den Modus Dynamisch ist das aber unbelegt, dort lief Min historisch immer auf 0.
- Für das Kippen nach 5,5 Minuten gibt es mehrere Erklärungskandidaten: eine Firmware-Plausibilitätsprüfung, die das degenerierte Fenster Min = Max verwirft und auf interne Defaults zurückfällt; ein generell anderes Regelverhalten im 2289-Kontext; oder ein Ablauf der externen Vorgaben (auffällige zeitliche Nähe der ~5,5 Minuten zum 300-s-Zyklus-Limit).
- Welcher Kandidat zutrifft, ist offen; getestet wurde nur diese eine Konstellation.

*Nachtrag (Web-Recherche 2026-07-03):*
Die Community-Quellen stützen den Befund und liefern eine plausible Erklärung.
Laut kohaku (PV-Forum Thread 206718 S. 23, 2024-11-16) lädt Modus 2289 grundsätzlich nur bei Einspeisung am Netzanschlusspunkt; ein Lade-Zwang ist in diesem Modus nicht vorgesehen.
Für das 5,5-Minuten-Kippen kommen zwei dokumentierte Timeout-Mechanismen im selben Zeitfenster in Frage (300-s-Erneuerungspflicht der BMS-Register; ~5-min-Rückfall der externen Steuerung).
Details und Quellen im Abschnitt "Community-Wissen & Quellenlage" unten.

**Reaktion im Adapter:** "Akku Netzladen" nutzt ab v1.5.0 deshalb dieselbe 40151/40149-Kommandoschiene wie
"Akku schnell Laden" statt der BMS-Leistungsgrenzen-Register (40793–40801/41259).
Der oben dokumentierte v1.3.0-Spike-Mechanismus betraf ausschließlich den BMS-Leistungsgrenzen-Pfad und ist
für "Akku Netzladen" damit nicht mehr relevant – der 40151/40149-Pfad zeigte im Live-Test kein Spike-Verhalten.
Eine Restunsicherheit bleibt: der konkrete Übergang "nur Entladen"/"Pause" → "Akku Netzladen" wurde noch
nicht gezielt auf einen Leistungs-Spike geprüft.
Empfehlung für Produktiv-Rollout: diesen Übergang einmal beobachten, auch wenn das Restrisiko nach der
Mechanik-Umstellung als gering einzuschätzen ist.

**Sperr-Modi: 0-W-Fenster als zusätzliche Verteidigungslinie neben den OpMod-Flags (Härtung 2026-07-12):**
Beim baugleichen Huawei-Adapter zeigte ein Gerätetest (Projekt ha-hesselmann, Befund G2), dass ein reines Verbots-Flag den Akku nicht am Laden hinderte; hart wirkten dort nur 0-W-Leistungsgrenzen.
Für SMA ist die Entlade-Sperre über `BatDschMaxW` = 0 Community-erprobt (evcc-"hold"-Modus, siehe oben); die Lade-Sperre über `BatChaMaxW` = 0 folgt derselben Fenster-Semantik, ist am STP SE aber **nicht durch eigenen Gerätetest belegt**.
Der Adapter schreibt deshalb seit der Härtung in den Sperr-Modi das jeweils verbotene Fenster als `[0, 0]` (Pause: beide Fenster) statt unconditional positiver Werte; die OpMod-Flags 303/2289/2290 bleiben zusätzlich gesetzt.
Beides gilt bis zu bestandenen Gerätetests als unbewiesen; die Tests (siehe `docs/geraetetests-haertung-2026-07.md`) sind Release-Gate.
Ein Write-Readback zur Verifikation ist nicht möglich, weil die Schreibregister flüchtig sind und als 0/null zurücklesen (siehe "Persistenz" im Community-Abschnitt); die Überwachung übernimmt der Wächter-Blueprint (`sma_stp_se_wachter.yaml`) verhaltensbasiert über die Ist-Leistungssensoren 31393/31395.
Bekannte Rest-Lücke: ein evcc-Nutzer beobachtete kurze Entlade-Bursts trotz `BatDschMaxW` = 0 während Wallbox-Schnellladen (Issue #18339, ungelöst geschlossen) - genau solche Fälle meldet der Wächter.
Offener Gerätetest zum Handoff: Verhalten der 40149-Kommandoschiene, wenn zuvor `[0, 0]`-Fenster + Sperr-OpMod geschrieben wurden; der Adapter schreibt beim Wechsel Sperr-Modus → Kommando-/Automatik-Modus deshalb einmalig ein offenes Freigabe-Set (Fenster offen, OpMod 1438), erkannt über den Modus-Tracker im Schreibwert-Helfer.

**Für eigene Nutzung der BMS-Leistungsgrenzen-Register (40793–40801):**
Als Grenzfenster (Min = 0, Max als Deckel) im Modus Dynamisch sind die Register erprobt und die empfohlene Nutzung.
Wer sie darüber hinaus als aktive Ladesteuerung einsetzen will (insbesondere Min > 0 oder Min = Max), sollte das Verhalten am eigenen WR selbst verifizieren - der Befund oben zeigt, dass das mindestens im 2289-Kontext nicht funktioniert.

---

## Community-Wissen & Quellenlage (Web-Recherche, Stand 2026-07-03)

> Dieser Abschnitt fasst externe Quellen zusammen (Photovoltaikforum, ioBroker-Forum, loxforum, evcc auf GitHub).
> Community-Aussagen sind als solche gekennzeichnet und nicht an dieser Anlage verifiziert, sofern nicht anders vermerkt.

### Fenster-Semantik von 40793-40801: durch Community-Berichte gestützt

Die Einordnung der vier Min-/Max-Register als Grenzen der WR-eigenen Regelung (nicht als Sollwerte) deckt sich mit der Community.
humi208 beschreibt sie als Limits, nicht als Kommandos ([PV-Forum Thread 244594](https://www.photovoltaikforum.com/thread/244594-sma-modbus-welche-register-nutzt-ihr/), 2025-03-18).
Das evcc-Projekt nutzt sie im "normal"-Modus genauso wie dieser Adapter: Min = 0, Max als Deckel, `GridWSpt` = 0, zyklisch erneuert ([sma-hybrid Template](https://github.com/evcc-io/evcc/blob/master/templates/definition/meter/sma-hybrid.yaml)).
Wichtig: Einzelne Max-Register isoliert zu schreiben zeigt keine Wirkung.
Mehrere Nutzer berichten, dass 40795/40799 allein beschrieben wirkungslos blieben (kohaku/seifranudo, [PV-Forum Thread 194071](https://www.photovoltaikforum.com/thread/194071-tripower-smart-energy-begrenzung-der-ladeleistung-des-speichers-%C3%BCber-modbus/), 2023; tuning/Delphinis, [ioBroker-Forum Topic 59635](https://forum.iobroker.net/topic/59635/sma-hybrid-wechselrichter-stp10-0-3se-40-modbus-schreiben), 2022/2024).
Wirkung entfaltet die Registerfamilie erst als komplett geschriebenes Set inkl. `CmpBMS.OpMod` und `GridWSpt` (kohaku, [PV-Forum Thread 206718, S. 23](https://www.photovoltaikforum.com/thread/206718-sma-stp10-0-3se-40-welcher-modbus-register-zum-laden-der-batterie/?pageNo=23), 2024-11-16).
Der Unterschied zur 40149/40151-Schiene wird in der Community genauso beschrieben wie hier: 40149 ist ein direkter Leistungssollwert ("positiv = entladen, negativ = laden", arteck, ioBroker-Forum Topic 59635, 2024-10-28), die CmpBMS-Familie parametriert dagegen die WR-eigene Regelung am Netzanschlusspunkt.

### Netzladen via 2289 + Min=Max: evcc nutzt exakt dieses Rezept, mit gemischten Ergebnissen

Das evcc-Template `sma-hybrid` setzt für den Modus "charge" exakt die Kombination, die in unserem Live-Test scheiterte: `OpMod` = 2289, `BatChaMinW` = `BatChaMaxW` = chargepower, `DschMin/Max` = 0, `GridWSpt` = 0 (eingeführt mit [PR #17393](https://github.com/evcc-io/evcc/pull/17393), 2024-11-25; evcc nutzt 40236 statt 41259 und 2424 statt 1438 als Normalmodus).
Mindestens ein Nutzer bestätigt damit funktionierendes Netzladen (Aarfalke, [PV-Forum Thread 252168](https://www.photovoltaikforum.com/thread/252168-preisabh%C3%A4ngiges-laden-der-batterie-%C3%BCber-modbus-tcp/), 2025-09-21).
Andere berichten genau unser Symptom, dass die Batterie statt zu laden nur in Standby geht ([evcc Issue #17115](https://github.com/evcc-io/evcc/issues/17115), 2024; [Issue #15442](https://github.com/evcc-io/evcc/issues/15442), 2024-08-17).
Wesentlicher Unterschied zu unserem Test: evcc schreibt das komplette Registerset per Watchdog alle 60 s neu (Template-Default).
Einordnung: Wegen der 2289-Semantik (lädt nur bei Einspeisung) ist dieses Rezept auch mit kurzem Schreibzyklus kein garantiertes Netzladen; der 40151/40149-Pfad bleibt die robustere Schiene für erzwungenes Laden (deckt sich mit unserem Live-Test und mit arteck, ioBroker-Forum Topic 59635, 2024-10-28).
Widerspruch in den Quellen: kohaku beschreibt 303/308/2424 pauschal als "weder geladen noch entladen", während evcc 2424 produktiv als Normalmodus (WR-eigene Regelung innerhalb der Fenster) nutzt.
Welche Beschreibung exakt stimmt, ist offen; dieser Adapter nutzt weiterhin 1438 (Auto) als Normalmodus, was live belegt funktioniert.

### Timeouts & Zykluszeiten

- BMS-Registerfamilie (40793-40801 + OpMod): alle Register innerhalb von 10 s schreiben, Erneuerung mindestens alle 300 s (kohaku, PV-Forum Thread 206718 S. 23, 2024-11-16; deckt sich mit der SMA-Support-Antwort bei ajay123).
- 40151 (externe Steuerung): fällt ohne erneutes Schreiben nach ca. 5 min zurück; Empfehlung: alle 4 min neu schreiben (Kumpane, PV-Forum Thread 206718 S. 4, 2023-11-02).
- Der Rückfall-Timeout ist als Geräteparameter "Externe Wirkleistungsvorgabe, Timeout" einstellbar (5 s bis 9 h); nach Ablauf kehrt der WR zur **internen Regelung** zurück (kohaku, ebd.).
- Firmware-abhängige Defaults berichtet: 30 min (FW 3.1.9R), 10 min (FW 3.2.20R) (kohaku, PV-Forum Thread 194071, 2023-04-21).
- Praktizierte Zykluszeiten: evcc-Watchdog 60 s; arteck alle 10 s; kohaku testete 2-3 s als stabiles Minimum und warnt vor 500-ms-Zyklen; wittmannchris und Maverick78de legen 1-2 s Pause zwischen Registergruppen ein, um den Modbus nicht zu überlasten ([evcc Issue #15881](https://github.com/evcc-io/evcc/issues/15881), 2024-09-03).
- Einordnung zu unserem 5,5-min-Kipp-Effekt: Ein exakter Beleg für 5,5 min findet sich nicht, aber zwei dokumentierte Mechanismen liegen genau in diesem Zeitfenster (300-s-Erneuerungspflicht der BMS-Register; ~5-min-Rückfall von 40151).
- Das beobachtete ungeregelte Volllast-Laden hat damit eine plausible (aber nicht direkt belegte) Erklärung: Nach dem Rückfall auf die interne Regelung lädt der WR schlicht den vollen PV-Überschuss, ohne die abgelaufenen externen Fenster.

### Entlade-Deckel und Entlade-Sperre (40799)

- Community-Standard für den Entlade-Deckel entspricht unserem Muster: `BatDschMinW` = 0, `BatDschMaxW` = Deckel, zyklisch erneuert (evcc sma-hybrid; wittmannchris, evcc Issue #15881: 40799 = 2650 im Normalbetrieb).
- Entlade-Sperre wird über `BatDschMaxW` = 0 realisiert (evcc "hold"-Modus).
- Bekannte Eigenheit: Ein Nutzer mit STP10.0-3SE-40 (FW 3.05.26.R) berichtet, dass die Sperre während Wallbox-Schnellladen wiederholt kurz durchbrach (Entlade-Bursts bis ~4,1 kW trotz 40799 = 0); das Issue wurde ungelöst geschlossen ([evcc Issue #18339](https://github.com/evcc-io/evcc/issues/18339), 2025-01-21).
- Eine zwingende Reihenfolge Min-vor-Max ist nirgends dokumentiert; evcc schreibt OpMod zuerst, dann ChaMin, ChaMax, DschMin, DschMax, GridWSpt.
- Zum Verhalten bei Min > Max wurde keine Quelle gefunden.
- Persistenz über WR-Neustarts ist nirgends belegt; die Schreibregister sind flüchtig (lesen als 0/null zurück: arteck/M_aus_B, ioBroker-Forum Topic 59635) und laufen ohnehin über Timeouts aus.
- Nach einem Neustart ist daher von Normalbetrieb auszugehen, bis der nächste Schreibzyklus greift.

### Weitere Fallstricke aus den Quellen

- SHM2-Firmware: Mit SHM-Firmware 2.14.x überschreibt der Home Manager die Modbus-Batteriesteuerung am WR; ab 2.15.x koexistiert es (humi208, PV-Forum Thread 206718 S. 23, 2024-10-09).
- Die offizielle Parameterliste enthält Duplikat-Adressen (44427 für 40151, 44433/44437 für 40795/40799), die in Community-Tests wirkungslos blieben (tuning, ioBroker-Forum Topic 59635, 2022-11-03).
- 40149-Encoding: Wird das Register im Client als signed 32-bit (Big Endian) konfiguriert, entfällt das manuelle 65535-Encoding; Fehlversuche mit manuellem Zweierkomplement gingen auf falsche Registerkonfiguration zurück (f.eckel, [PV-Forum Thread 226189](https://www.photovoltaikforum.com/thread/226189-modbus-40149-negative-werte/), 2024-04-16).
- Off-by-one-Falle: Manche Modbus-CLIs adressieren 0-basiert; dort landet man z.B. bei 40150/40152 statt 40149/40151 (Beispiel in [evcc Issue #15442](https://github.com/evcc-io/evcc/issues/15442)).
- **Register 40210 als "Hauptschalter" für externe Vorgabe:** In einem Fall (2026-06), in dem der WR `CmpBMS.OpMod` 1438 strikt ablehnte, half das vorherige Setzen von 40210 (`Inverter.WModCfg.WMod`) auf `[0, 1079]` = externe Leistungsvorgabe (LumpiStefan an amarok12, [PV-Forum Thread 156613, S. 24](https://www.photovoltaikforum.com/thread/156613-sbs-manuelle-steuerung-durch-modbus/?pageNo=24), 2026-06-20). Die Ablehnung war dort am Rückgabewert `0x00FFFFFD` (16777213) erkennbar - SMAs Code für "nicht unterstützt / gesperrt" (derselbe Wert, der auch im Betriebsstatus 33003 als "Information liegt nicht vor" auftaucht). ⚠️ 40210 ist ein persistierter RW-Parameter - falls überhaupt nötig, einmalig setzen, nicht zyklisch. Auf Anlagen, auf denen die CmpBMS-Steuerung bereits funktioniert (wie unserer), ist er offenbar schon passend konfiguriert; als Diagnose-Punkt bei "WR nimmt OpMod nicht an" aber wertvoll. Derselbe Thread bestätigt außerdem den reinen Min/Max-Fenster-Ansatz ohne `GridWSpt`-Verschiebung als gangbare Steuervariante (amarok12/Chris, S. 25, 2026-06-22).

### Offizielle Parameterliste

SMA stellt die Parameter-/Modbus-Liste für den STP SE als HTML-Export bereit: `PARAMETER-HTML_STPxx-3SE-40_30109R_V11.zip` über files.sma.de (laut kohaku Stand Mai 2026 die letzte offizielle Dokumentation, [PV-Forum Thread 260874](https://www.photovoltaikforum.com/thread/260874-sunny-tripower-8-0-se-firmware-version-3-5-29-r-dokumentation-zu-modbus-register/), 2026-05-19).
rewalde bestätigt dort (ebd., 2026-05-19) die Lücken, die auch diese Doku nennt: 40795/40799 sind offiziell dokumentiert, 40793/40797/40801/40236 nicht.

---

## Quellen

- **ajay123** im Photovoltaikforum: [Direkte SMA-Support-Antwort mit offiziellen Registernamen](https://www.photovoltaikforum.com/thread/215473-begrenzen-der-lade-entladeleistung-byd-mit-stp-se/?postID=4033278#post4033278) *(Hauptquelle für die BMS-Register)*
- **Skybarks** im Photovoltaikforum: [Hinweis auf offizielle SMA Modbus-Dokumentation](https://www.photovoltaikforum.com/thread/206718-sma-stp10-0-3se-40-welcher-modbus-register-zum-laden-der-batterie/?pageNo=6)
- **Community-Sammlung** im Photovoltaikforum: [SMA Modbus – Welche Register nutzt ihr?](https://www.photovoltaikforum.com/thread/244594-sma-modbus-welche-register-nutzt-ihr/) *(SBS 2.5 Bestätigung, SHM2-Register, GGC-Deprecation)*
- **Maverick78de** auf GitHub: [SMA_forecast_charging](https://github.com/Maverick78de/SMA_forecast_charging) (ioBroker, archiviert 2023) *(SBS-3.7–10-Schreib-/Lese-Register und DevType-Zuordnung – `bat_regelung_2.3.4.js`)*
- **kohaku** im Photovoltaikforum: [Thread 206718, S. 23](https://www.photovoltaikforum.com/thread/206718-sma-stp10-0-3se-40-welcher-modbus-register-zum-laden-der-batterie/?pageNo=23) (2024-11-16) *(OpMod-Taglist inkl. 2424, 2289/2290-Semantik, 10-s-/300-s-Regel)* und [Thread 206718, S. 4](https://www.photovoltaikforum.com/thread/206718-sma-stp10-0-3se-40-welcher-modbus-register-zum-laden-der-batterie/?pageNo=4) (2023-11-02, mit Kumpane) *(40151-Rückfall, Timeout-Geräteparameter)*
- **Photovoltaikforum**: [Thread 194071 – Begrenzung der Ladeleistung über Modbus](https://www.photovoltaikforum.com/thread/194071-tripower-smart-energy-begrenzung-der-ladeleistung-des-speichers-%C3%BCber-modbus/) *(Max-Register isoliert wirkungslos, Firmware-Timeout-Defaults)* · [Thread 226189 – Modbus 40149 negative Werte](https://www.photovoltaikforum.com/thread/226189-modbus-40149-negative-werte/) *(S32-Encoding)* · [Thread 252168 – Preisabhängiges Laden](https://www.photovoltaikforum.com/thread/252168-preisabh%C3%A4ngiges-laden-der-batterie-%C3%BCber-modbus-tcp/) *(Netzladen via evcc)* · [Thread 260874 – Doku zu Modbus-Registern](https://www.photovoltaikforum.com/thread/260874-sunny-tripower-8-0-se-firmware-version-3-5-29-r-dokumentation-zu-modbus-register/) *(offizielle Parameterliste, Doku-Lücken)*
- **evcc** auf GitHub: [sma-hybrid Template](https://github.com/evcc-io/evcc/blob/master/templates/definition/meter/sma-hybrid.yaml) *(CmpBMS-Registernutzung, 60-s-Watchdog)* · [PR #17393](https://github.com/evcc-io/evcc/pull/17393) · Issues [#15881](https://github.com/evcc-io/evcc/issues/15881), [#17115](https://github.com/evcc-io/evcc/issues/17115), [#15442](https://github.com/evcc-io/evcc/issues/15442), [#18339](https://github.com/evcc-io/evcc/issues/18339)
- **ioBroker-Forum**: [Topic 59635 – STP10.0-3SE-40 Modbus Schreiben](https://forum.iobroker.net/topic/59635/sma-hybrid-wechselrichter-stp10-0-3se-40-modbus-schreiben) *(40149/40151-Praxis, flüchtige Register, 44433/44437 wirkungslos)*
- Offizielle SMA Modbus-Dokumentation: Parameterlisten-Export `PARAMETER-HTML_STPxx-3SE-40_30109R_V11.zip` via files.sma.de bzw. über das SMA Service-Portal (Registrierung erforderlich)

---

*Letzte Aktualisierung: Juli 2026 – Ergänzungen willkommen via Pull Request oder Issue.*
