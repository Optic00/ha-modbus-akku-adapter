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
   `configuration.yaml`, der den SMA STP SE per TCP einbindet.
   → Vorlage: [`examples/sma_modbus.example.yaml`](examples/sma_modbus.example.yaml) (nur die IP eintragen).
2. **Ein Steuer-Dropdown** `input_select.akkusteuerung_modus` mit **8 festen Optionen**
   (`Akku Automatisch`, `Akku Dynamisch`, `Akku Pause`, `Akku nur Laden`,
   `Akku nur Entladen`, `Akku schnell Laden`, `Akku schnell Entladen`, `Akku 0.2C Laden`)
   **plus 7 Zahlen-Helfer** (`input_number.*`) für die Lade-/Entlade-Leistungen in Watt.
   → Fertig zum Kopieren: [`examples/akkusteuerung_helpers.example.yaml`](examples/akkusteuerung_helpers.example.yaml).
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

Kopiere den `modbus:`-Block aus [`examples/sma_modbus.example.yaml`](examples/sma_modbus.example.yaml)
in deine `configuration.yaml` (oder ein Package) und trage die **IP-Adresse deines
Wechselrichters** ein. Der Hub heißt dort `sma-sr_wr` – diesen Namen brauchst du gleich
beim Blueprint wieder.

> ℹ️ Modbus-Steuerung ohne Grid-Guard-Code setzt je nach Gerät deaktivierte Updates oder
> Beta-Firmware (ab ca. 3.06.xx) voraus – siehe Kommentar in der Beispieldatei.

### Schritt 2 – Helfer anlegen (Dropdown + Leistungswerte)

Der Adapter liest seine Befehle aus Home-Assistant-Helfern. Kopiere dafür den Inhalt von
[`examples/akkusteuerung_helpers.example.yaml`](examples/akkusteuerung_helpers.example.yaml)
in deine `configuration.yaml` (oder Package) und starte HA neu. Du erhältst:

- **`input_select.akkusteuerung_modus`** – das Steuer-Dropdown mit den **8 festen Optionen**
  (exakte Schreibweise, sonst greift der Adapter nicht):
  `Akku Automatisch` · `Akku Dynamisch` · `Akku Pause` · `Akku nur Laden` ·
  `Akku nur Entladen` · `Akku schnell Laden` · `Akku schnell Entladen` · `Akku 0.2C Laden`
- **7 `input_number.*`-Helfer** (Watt) für die Lade-/Entlade-Sollwerte und Min/Max-Grenzen.

Zusätzlich erwartet das Blueprint noch zwei anlagenspezifische Sensoren (Details + Beispiel
in der Helfer-Datei):

- **WR-Betriebsstatus-Sensor**, der `"Ok"` liefert, wenn der WR bereit ist (der rohe
  Modbus-Sensor gibt nur Zahlen zurück → per Template auf `"Ok"` mappen).
- **Sensor „Dynamische Ladestärke"** (Watt) – kommt von deiner *Strategie* (Schritt 3) bzw.
  dem Schwesterprojekt; alternativ ein eigener Template-Sensor, der eine Watt-Zahl ausgibt.

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
auswählen.

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
