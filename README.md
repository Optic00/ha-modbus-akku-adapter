# ha-modbus-akku-adapter

Dünne **Hardware-Adapter** (Home-Assistant-Blueprints), die einen abstrakten
Steuer-**Modus** in konkrete **Modbus-Register-Schreibvorgänge** für Batterie-Hybrid-
Wechselrichter übersetzen. Aktuell: **SMA STP SE Hybrid**. Geplant: **SMA SBS**, später
andere Marken (z. B. Huawei).

> 🎯 **Idee:** Strategie (wann soll geladen/entladen werden) und Hardware-Ansteuerung
> (wie wird es am konkreten WR umgesetzt) sind getrennt. Wer schon eine **eigene
> Akkusteuerung** hat, kann **nur diesen Adapter** nutzen, um seine Entscheidungen sauber
> auf Modbus umzusetzen. Das Bindeglied ist der [Modus-Contract](docs/modus-contract.md).

> ⚠️ **Disclaimer:** Inoffizielle Community-Lösung. Wird in **keiner** Weise von SMA
> Solar Technology AG begleitet, geprüft oder supportet. Das direkte Beschreiben von
> Modbus-Registern kann WR/Batterie/Anlage beschädigen, Garantie kosten oder
> gefährliche Betriebszustände erzeugen. **Nutzung auf eigene Gefahr.**

---

## Was du brauchst (Überblick für Einsteiger)

Das Blueprint ist nur der **Übersetzer**. Damit es etwas zu übersetzen hat, müssen in
Home Assistant **vorher** drei Dinge existieren. Reihenfolge:

1. **Modbus-Verbindung zum Wechselrichter** – ein `modbus:`-Block in deiner
   `configuration.yaml`, der den SMA STP SE per TCP einbindet. (Modbus ist der
   **einzige** Teil, der zwingend YAML braucht – HA hat dafür keine Oberfläche.)
   → Vorlage: [`examples/sma_modbus.example.yaml`](examples/sma_modbus.example.yaml) (nur die IP eintragen).
2. **Ein paar Helfer**, die du komplett **über die HA-Oberfläche** anlegen kannst:
   ein Steuer-Dropdown `input_select.akkusteuerung_modus` mit **8 festen Optionen**
   (`Akku Automatisch`, `Akku Dynamisch`, `Akku Pause`, `Akku nur Laden`,
   `Akku nur Entladen`, `Akku schnell Laden`, `Akku schnell Entladen`, `Akku 0.2C Laden`)
   **plus 6 Zahlen-Helfer** (`input_number.*`) für die Lade-/Entlade-Leistungen in Watt.
   (Der 0.2C-Wert wird automatisch aus der Batteriekapazität berechnet – kein Feld nötig.)
   → Lieber kopieren statt klicken? [`examples/akkusteuerung_helpers.example.yaml`](examples/akkusteuerung_helpers.example.yaml).
3. **Etwas, das das Dropdown umschaltet** – also eine *Strategie*. Das kann eine eigene
   Automation sein oder das Schwesterprojekt
   [`ha-opti-akkusteuerung`](https://github.com/Optic00/ha-opti-akkusteuerung).

**Erst danach** importierst du das Blueprint (Schritt unten) und verbindest es mit diesen
Helfern. Ohne Schritt 1–2 hat das Blueprint nichts, worauf es schreiben kann, und
beschwert sich beim Speichern über fehlende Entitäten.

```
Strategie  →  input_select.akkusteuerung_modus  →  [ DIESES BLUEPRINT ]  →  Modbus-Register  →  SMA-WR
(setzt Modus)        (+ input_number.* in W)            übersetzt
```

---

## Einrichtung – Schritt für Schritt

### Schritt 1 – Modbus-Verbindung zum WR (`configuration.yaml`)

Dieser Schritt geht **nur über YAML** – Home Assistant bietet für die Modbus-Integration
keine grafische Oberfläche. Kopiere den `modbus:`-Block aus
[`examples/sma_modbus.example.yaml`](examples/sma_modbus.example.yaml) in deine
`configuration.yaml` (oder ein Package) und trage die **IP-Adresse deines Wechselrichters**
ein. Der Hub heißt dort `sma-sr_wr` – diesen Namen brauchst du gleich beim Blueprint wieder.

Die Beispieldatei bringt auch den Sensor **Batterie-Nennkapazität** (Register 40187) mit.
Daraus berechnet der Adapter den Modus „Akku 0.2C Laden" automatisch (0,2 × Kapazität) –
du musst dafür **nichts** von Hand eintragen.

> ℹ️ Modbus-Steuerung ohne Grid-Guard-Code setzt je nach Gerät deaktivierte Updates oder
> Beta-Firmware (ab ca. 3.06.xx) voraus – siehe Kommentar in der Beispieldatei.

### Schritt 2 – Helfer anlegen (über die Oberfläche)

Diese Helfer legst du komplett per GUI an – **kein YAML nötig**. Pfad:
*Einstellungen → Geräte & Dienste → Helfer → ➕ Helfer erstellen*.

> ⚠️ **Wichtig:** Das Blueprint sucht die Helfer an **exakten Entity-IDs**. Tippe die Namen
> genau wie unten (mit `ae` statt `ä`!), dann erzeugt HA automatisch die richtige ID.
> Sonst macht HA aus „Ladestärke" die ID `…ladestarke…` statt `…ladestaerke…` und der
> Adapter findet den Helfer nicht. (Die Entity-ID lässt sich notfalls nachträglich im
> Helfer über das Zahnrad korrigieren.)

**a) Das Steuer-Dropdown** – Typ **„Auswahl"**, Name `Akkusteuerung Modus`. Trage als
Optionen **exakt** diese 8 Werte ein (Reihenfolge egal, Schreibweise nicht):

```
Akku Automatisch
Akku Dynamisch
Akku Pause
Akku nur Laden
Akku nur Entladen
Akku schnell Laden
Akku schnell Entladen
Akku 0.2C Laden
```

**b) Die 6 Leistungs-Helfer** – jeweils Typ **„Zahl"**, Einheit `W`, Min `0`, Max z. B.
`11000`. Name genau so eintippen → ergibt die benötigte Entity-ID:

| Name eintippen | ergibt Entity-ID | wofür |
|---|---|---|
| `Akkusteuerung Ladestaerke Soll` | `input_number.akkusteuerung_ladestaerke_soll` | „schnell Laden" |
| `Akkusteuerung Entladestaerke Soll` | `input_number.akkusteuerung_entladestaerke_soll` | „schnell Entladen" |
| `Akkusteuerung Min Ladestaerke` | `input_number.akkusteuerung_min_ladestaerke` | Untergrenze Laden |
| `Akkusteuerung Max Ladestaerke` | `input_number.akkusteuerung_max_ladestaerke` | Obergrenze Laden |
| `Akkusteuerung Min Entladestaerke` | `input_number.akkusteuerung_min_entladestaerke` | Untergrenze Entladen |
| `Akkusteuerung Max Entladestaerke` | `input_number.akkusteuerung_max_entladestaerke` | Obergrenze Entladen |

> 0.2C braucht **keinen** eigenen Helfer – der Wert kommt automatisch aus der Kapazität
> (Schritt 1).

**c) Der WR-Status-Sensor** – Typ **„Vorlage" → „Vorlage eines Sensors"**. Er muss `"Ok"`
liefern, wenn der WR bereit ist (der rohe Modbus-Sensor gibt nur Zahlen zurück). Vorlage:

```jinja
{% set s = states('sensor.sma_stp_se_33003_betriebsstatus') | int(0) %}
{{ 'Ok' if s in [235, 1463] else 'nicht bereit' }}
```

**d) Der Sensor „Dynamische Ladestärke" (Watt)** kommt **nicht** aus diesem Repo, sondern
von deiner *Strategie* (Schritt 3) bzw. dem Schwesterprojekt – oder du baust einen eigenen
Template-Sensor, der einfach eine Watt-Zahl ausgibt.

> 💡 **Lieber kopieren statt klicken?** Dieselben Helfer (Dropdown + 6 Zahlen) gibt es fertig
> als YAML in [`examples/akkusteuerung_helpers.example.yaml`](examples/akkusteuerung_helpers.example.yaml) –
> dort sind die Entity-IDs garantiert korrekt.

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

### Schritt 3 – Strategie, die das Dropdown umschaltet

Irgendetwas muss `input_select.akkusteuerung_modus` setzen – sonst steht der Adapter still.
Das ist deine **eigene Automation** oder das Schwesterprojekt
[`ha-opti-akkusteuerung`](https://github.com/Optic00/ha-opti-akkusteuerung). Zum Testen
reicht es, das Dropdown von Hand umzuschalten.

### Schritt 4 – Blueprint importieren und verbinden

**Erst jetzt** – wenn Schritt 1–2 stehen – das Blueprint importieren. Es wird **HA-nativ per
Raw-URL** importiert (kein HACS nötig – HACS hat keine Blueprint-Kategorie):
*Einstellungen → Automatisierungen & Szenen → Blueprints → Blueprint importieren* → Raw-URL
einfügen, dann eine Automation aus dem Blueprint anlegen und die Helfer aus Schritt 1–2
auswählen. Die Inputs (Hub-Name, Status-Sensor, **Batterie-Nennkapazität**, Dynamik-Sensor,
Modus-Select) haben sinnvolle Defaults – prüfe sie und passe sie bei abweichenden
Entity-Namen an.

| WR-Familie | Blueprint | Raw-URL (Import) | Status |
|---|---|---|---|
| **SMA STP SE Hybrid** | `sma_stp_se_adapter.yaml` | `https://raw.githubusercontent.com/Optic00/ha-modbus-akku-adapter/main/blueprints/automation/akku_adapter/sma_stp_se_adapter.yaml` | ✅ live getestet |
| SMA SBS | `sma_sbs_adapter.yaml` | – | 🧪 geplant (Register-Map abweichend) |
| Andere (z. B. Huawei) | – | – | 💬 offen |

## Dokumentation

- [`docs/modus-contract.md`](docs/modus-contract.md) – die stabile Schnittstelle Strategie ⇄ Adapter (Modus-Vokabular).
- [`docs/modbus-register-referenz.md`](docs/modbus-register-referenz.md) – inoffizielle SMA-Modbus-Registerreferenz (Community).

## Sicherheits-Grundregeln

- **Single-Writer:** Zu jedem Zeitpunkt darf **nur EINE** Automation den WR via Modbus
  schreiben. Alten Adapter/Steuerung deaktivieren, bevor dieser aktiviert wird.
- **Min < Max:** Der Adapter setzt Min-Ladeleistung vor der Max-Leistung (Guard).
- Werte vor Produktivbetrieb an der eigenen Anlage prüfen (Register/Encoding können je
  Firmware abweichen).

## Lizenz

[MIT](LICENSE) – Nutzung auf eigene Gefahr (siehe Disclaimer oben).
