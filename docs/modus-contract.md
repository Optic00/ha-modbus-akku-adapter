# Modus-Contract – Strategie ⇄ Hardware-Adapter

Dieses Projekt trennt **Strategie** (was soll passieren) von **Hardware-Adapter**
(wie wird es am konkreten Wechselrichter umgesetzt). Das Bindeglied ist ein
abstrakter **Modus** in einem `input_select` (Standard:
`input_select.akkusteuerung_modus`) plus einige Helfer. Ziel: ein neuer
Wechselrichter (z. B. Huawei) braucht **nur einen neuen Adapter-Blueprint** –
Strategie und Helfer bleiben unverändert.

> Leitlinie (bewusst klein halten): Der Contract ist **zielorientiert**, nicht
> register-/herstellernah. Erst wenn ein realer zweiter Adapter (Huawei) existiert,
> wird geprüft, ob 1–2 Begriffe ergänzt werden müssen. Kein WR-Modell auf Vorrat.

## Rollen
- **Strategie** (`automations/opti_strategie.yaml` im Repo `ha-opti-akkusteuerung`,
  **kein Blueprint** — editierbare Automation): entscheidet anhand von Prognose,
  Preis und Ziel-SoC und **setzt** den Modus (`input_select.select_option`).
- **Adapter-Blueprint** (z. B. `sma_stp_se_adapter.yaml`): **liest** den Modus +
  Sollwerte und übersetzt sie hardware-spezifisch (bei SMA: Modbus-Register).
- Der Adapter nimmt den Modus-Select als `!input mode_select` entgegen → wiederverwendbar
  für jede Strategie, die dasselbe `input_select` setzt.

## Modus-Vokabular (Contract)

| Option (UI, deutsch) | Bedeutung | Zusatz-Parameter |
|---|---|---|
| `Akku Automatisch` | WR-Eigenregelung / Standard | – |
| `Akku Dynamisch` | Adapter regelt auf Ziel (SoC/Leistungsgrenzen) | min/max SoC, Grenzen |
| `Akku Pause` | weder laden noch entladen | – |
| `Akku nur Laden` | Entladen gesperrt | – |
| `Akku Netzladen` | Entladen gesperrt + erzwungenes dynamisches Laden (Mindestladung = dynamisches Ziel) | Ladeleistung (W), dynamisch |
| `Akku nur Entladen` | Laden gesperrt | – |
| `Akku schnell Laden` | erzwungenes Laden | Ladeleistung (W) |
| `Akku schnell Entladen` | erzwungenes Entladen | Entladeleistung (W) |
| `Akku 0.2C Laden` | UI-Preset → intern erzwungenes Laden mit normalisierter Leistung | Leistung aus 0.2C |

## Im Contract enthalten
- Der Modus (Vokabular oben).
- SoC-Grenzen: `input_number.minsoc`, `input_number.maxsoc`, Ziel via
  `sensor.opti_target_soc` (kanonischer Name; bei `ha-opti-akkusteuerung`
  in `packages/opti_derived.yaml` definiert).
- Abstrakte Leistungswünsche in **Watt** (Lade-/Entlade-/Limit-Leistung), kanonisch
  `sensor.opti_charge_power_w`.

## NICHT im Contract (gehört in den jeweiligen Adapter)
- Konkrete Register (SMA: 40149/40151/40793–40801/41259), OpMod-Werte.
- Schreibreihenfolge, Delays, Vorzeichenkonventionen, 32-bit-Encoding.
- Hersteller-Entity-Namen.
- `0.2C` als Roh-Modus – intern in W/% normalisieren.

## Später: Capability-Schicht (noch nicht implementiert)
Nicht jeder WR kann jeden Modus gleich gut. Ein Adapter sollte perspektivisch
seine Fähigkeiten melden (kann Netzladen, kann Entladen sperren, kann Ladeleistung
setzen, kann Export verhindern, braucht Sequenzierung), damit die Strategie nicht
annimmt, ein Wunsch sei umgesetzt, obwohl der WR ihn nur teilweise unterstützt.
Der Adapter darf Wünsche **clampen, ignorieren, sequenzieren, verzögert anwenden**
und Fehlerzustände melden. → Erst mit dem ersten Nicht-SMA-Adapter ausbauen.
