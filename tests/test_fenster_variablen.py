"""Host-unabhängige Tests der Jinja-Fenster-Variablen des SMA-Adapters.

Rendert die variables:-Sektion des Blueprints sequenziell (wie HA) mit
gemockten states()/now() und prüft die Sperr-Semantik (Härtung P1) und die
Grenzfenster-Invariante (Min nie == Max > 0).

Benötigt: PyYAML, jinja2, pytest (z. B. via venv des Schwester-Repos
ha-opti-akkusteuerung).
"""
import ast
from datetime import datetime, timezone
from pathlib import Path

import jinja2
import pytest
import yaml

BLUEPRINT = (
    Path(__file__).parent.parent
    / "blueprints/automation/akku_adapter/sma_stp_se_adapter.yaml"
)

FIXED_NOW = datetime(2026, 7, 12, 12, 0, 0, tzinfo=timezone.utc)

DEFAULT_STATES = {
    "input_select.akkusteuerung_modus": "Akku Dynamisch",
    "sensor.opti_charge_power_w": "3000",
    "input_number.akkusteuerung_min_ladestaerke": "200",
    "input_number.akkusteuerung_min_entladestaerke": "100",
    "input_number.akkusteuerung_max_entladestaerke": "2500",
}


class FakeState:
    def __init__(self, value, last_changed):
        self.state = value
        self.last_changed = last_changed


class FakeStates:
    """states('x') als Funktion UND states['x'].last_changed als Mapping."""

    def __init__(self, mapping, last_changed):
        self._m = mapping
        self._lc = last_changed

    def __call__(self, entity_id):
        return self._m.get(entity_id, "unknown")

    def __getitem__(self, entity_id):
        return FakeState(self._m.get(entity_id, "unknown"), self._lc)


def _input_constructor(loader, node):
    return f"INPUT:{loader.construct_scalar(node)}"


class BlueprintLoader(yaml.SafeLoader):
    pass


BlueprintLoader.add_constructor("!input", _input_constructor)


def load_blueprint():
    return yaml.load(BLUEPRINT.read_text(), Loader=BlueprintLoader)


def render_adapter_vars(mode, overrides=None, mode_age_seconds=3600):
    states_map = dict(DEFAULT_STATES)
    states_map["input_select.akkusteuerung_modus"] = mode
    states_map.update(overrides or {})
    last_changed = FIXED_NOW.timestamp() - mode_age_seconds

    env = jinja2.Environment()
    env.globals["now"] = lambda: FIXED_NOW
    env.globals["as_timestamp"] = (
        lambda v: v if isinstance(v, (int, float)) else v.timestamp()
    )
    env.globals["states"] = FakeStates(states_map, last_changed)

    bp = load_blueprint()
    ctx = {}
    for name, template in bp["variables"].items():
        if not isinstance(template, str) or (
            "{{" not in template and "{%" not in template
        ):
            # !input-Referenzen auf echte Entity-IDs mappen, Literale durchreichen.
            if isinstance(template, str) and template.startswith("INPUT:"):
                ctx[name] = {
                    "INPUT:mode_select": "input_select.akkusteuerung_modus",
                    "INPUT:dynamic_charge_strength_sensor": "sensor.opti_charge_power_w",
                }.get(template, template)
            else:
                ctx[name] = template
            continue
        rendered = env.from_string(template).render(**ctx)
        try:
            ctx[name] = ast.literal_eval(rendered)
        except (ValueError, SyntaxError):
            ctx[name] = rendered
    return ctx


# ---- P1: Sperr-Modi erzwingen [0, 0] im verbotenen Fenster ----


def test_pause_sperrt_beide_fenster():
    v = render_adapter_vars("Akku Pause")
    assert (v["v_40793"], v["v_40795"], v["v_40797"], v["v_40799"]) == (0, 0, 0, 0)


def test_nur_laden_sperrt_entladefenster():
    v = render_adapter_vars("Akku nur Laden")
    assert (v["v_40797"], v["v_40799"]) == (0, 0)
    assert v["v_40795"] == 3000
    assert v["v_40793"] == 200


def test_nur_entladen_sperrt_ladefenster():
    v = render_adapter_vars("Akku nur Entladen")
    assert (v["v_40793"], v["v_40795"]) == (0, 0)
    assert v["v_40799"] == 2500
    assert v["v_40797"] == 100


def test_dynamisch_bleibt_offen():
    v = render_adapter_vars("Akku Dynamisch")
    assert v["v_40795"] == 3000
    assert v["v_40799"] == 2500


def test_dynamisch_settling_cap_bleibt_erhalten():
    v = render_adapter_vars("Akku Dynamisch", mode_age_seconds=60)
    assert v["v_40795"] == 500


# ---- Grenzfenster-Invariante: Min nie == Max > 0 ----


@pytest.mark.parametrize(
    "mode", ["Akku Pause", "Akku nur Laden", "Akku nur Entladen", "Akku Dynamisch"]
)
@pytest.mark.parametrize(
    "charge_target,charge_floor",
    [("3000", "200"), ("100", "200"), ("0", "0"), ("200", "200")],
)
def test_invariante_min_nie_gleich_max_groesser_null(mode, charge_target, charge_floor):
    v = render_adapter_vars(
        mode,
        {
            "sensor.opti_charge_power_w": charge_target,
            "input_number.akkusteuerung_min_ladestaerke": charge_floor,
        },
    )
    assert not (v["v_40793"] == v["v_40795"] and v["v_40795"] > 0)
    assert not (v["v_40797"] == v["v_40799"] and v["v_40799"] > 0)
