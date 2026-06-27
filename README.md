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

## Adapter / Installation

Blueprints werden **HA-nativ per Raw-URL** importiert (kein HACS nötig –
HACS hat keine Blueprint-Kategorie). In HA: *Einstellungen → Automatisierungen &
Szenen → Blueprints → Blueprint importieren* → Raw-URL einfügen.

| WR-Familie | Blueprint | Raw-URL (Import) | Status |
|---|---|---|---|
| **SMA STP SE Hybrid** | `sma_stp_se_adapter.yaml` | `https://raw.githubusercontent.com/Optic00/ha-modbus-akku-adapter/main/blueprints/automation/akku_adapter/sma_stp_se_adapter.yaml` | ✅ live getestet |
| SMA SBS | `sma_sbs_adapter.yaml` | – | 🧪 geplant (Register-Map abweichend) |
| Andere (z. B. Huawei) | – | – | 💬 offen |

> Privates Repo: Raw-URLs funktionieren erst nach Veröffentlichung bzw. mit Token.

---

## Voraussetzungen

1. **Modbus-TCP-Hub** zum Wechselrichter – Vorlage: [`examples/sma_modbus.example.yaml`](examples/sma_modbus.example.yaml) (nur IP eintragen).
2. **Modus-`input_select`** + Sollwert-/SoC-Helfer gemäß [Modus-Contract](docs/modus-contract.md).
3. Eine **Strategie**, die den Modus setzt (eigene oder z. B. das Schwesterprojekt
   [`ha-opti-akkusteuerung`](https://github.com/Optic00/ha-opti-akkusteuerung)).

## Dokumentation

- [`docs/modus-contract.md`](docs/modus-contract.md) – die stabile Schnittstelle Strategie ⇄ Adapter (Modus-Vokabular).
- [`docs/modbus-register-referenz.md`](docs/modbus-register-referenz.md) – inoffizielle SMA-Modbus-Registerreferenz (Community).

## Sicherheits-Grundregeln

- **Single-Writer:** Zu jedem Zeitpunkt darf **nur EINE** Automation den WR via Modbus
  schreiben. Alten Adapter/Steuerung deaktivieren, bevor dieser aktiviert wird.
- **Min < Max:** Der Adapter setzt Min-Ladeleistung vor der Max-Leistung (Guard).
- Werte vor Produktivbetrieb an der eigenen Anlage prüfen (Register/Encoding können je
  Firmware abweichen).
