"""Strukturtests der Härtung 2026-07 (P2/P4, Review-Findings F2-F5).

Prüft die Action-Struktur des Blueprints: Schreibreihenfolge im Standardpfad,
Stale-Guard/Stale-Cleanup, CmpBMS-Freigabe, 40149-Klemmung, Tracker-Pflege
und den Automationsmodus.
"""
from test_fenster_variablen import load_blueprint

LOCK_MODES = ["Akku Pause", "Akku nur Laden", "Akku nur Entladen"]

KOMMANDO_BRANCHES = {
    "Wenn Akku schnell Laden": "Akku schnell Laden",
    "Wenn Akku schnell Entladen": "Akku schnell Entladen",
    "Wenn Akku Netzladen": "Akku Netzladen",
    'Bei "Akku 0.2C Laden"': "Akku 0.2C Laden",
}


def _top_level_writes(actions):
    return [
        a["data"]["address"]
        for a in actions
        if a.get("action") == "modbus.write_register"
    ]


def test_mode_queued_mit_silent():
    bp = load_blueprint()
    assert bp["mode"] == "queued"
    assert bp["max"] >= 2
    assert bp["max_exceeded"] == "silent"


def test_stale_guard_ist_erste_action():
    bp = load_blueprint()
    first = bp["actions"][0]
    assert first.get("condition") == "template"
    assert "run_modus" in first["value_template"]


def test_cmpbms_freigabe_vor_den_branches():
    bp = load_blueprint()
    second = bp["actions"][1]
    assert str(second.get("alias", "")).startswith("CmpBMS-Freigabe")
    addrs = [
        s["data"]["address"]
        for s in second["then"]
        if s.get("action") == "modbus.write_register"
    ]
    # Volles Set inkl. OpMod 1438, sonst wirkungslos (Community: nur als
    # komplett geschriebenes Set wirksam).
    assert addrs == [40793, 40795, 40797, 40799, 40801, 41259]
    opmod = [
        s
        for s in second["then"]
        if s.get("action") == "modbus.write_register"
        and s["data"]["address"] == 41259
    ][0]
    assert opmod["data"]["value"] == [0, 1438]


def test_standardpfad_reihenfolge_803_zuerst_opmod_zuletzt():
    """P2: geprüft und bewusst NICHT gedreht (Adversarial-Review 2026-07-12).

    803 neutralisiert zuerst die 40149-Schiene, dann kommen die (in
    Sperr-Modi restriktiven) Fensterregister, OpMod als Enable zuletzt.
    """
    bp = load_blueprint()
    actions = bp["actions"]
    top = _top_level_writes(actions)
    assert top == [40151, 40793, 40795, 40797, 40799, 40801]
    idx_40801 = max(
        i
        for i, a in enumerate(actions)
        if a.get("action") == "modbus.write_register"
    )
    opmod_aliases = {
        'Bei "Akku Pause"',
        'Bei "Akku nur Laden"',
        'Bei "Akku nur Entladen"',
        'Bei "Akku Dynamisch"',
    }
    opmod_idx = [
        i for i, a in enumerate(actions) if a.get("alias") in opmod_aliases
    ]
    assert len(opmod_idx) == 4 and all(i > idx_40801 for i in opmod_idx)


def test_stale_cleanup_in_allen_kommando_branches():
    """F4: bei Staleness nach 802 wird die Schiene deaktiviert (803), nicht
    einfach abgebrochen."""
    bp = load_blueprint()
    branches = {
        a.get("alias"): a for a in bp["actions"] if a.get("alias") in KOMMANDO_BRANCHES
    }
    assert len(branches) == len(KOMMANDO_BRANCHES)
    for alias, branch in branches.items():
        cleanups = [
            s
            for s in branch["then"]
            if str(s.get("alias", "")).startswith("Stale-Cleanup")
        ]
        assert len(cleanups) == 1, f"{alias}: kein Stale-Cleanup"
        cleanup = cleanups[0]
        writes = [
            s
            for s in cleanup["then"]
            if s.get("action") == "modbus.write_register"
        ]
        assert writes and writes[0]["data"]["address"] == 40151
        assert writes[0]["data"]["value"] == [0, 803]
        assert any("stop" in s for s in cleanup["then"])
        # Cleanup muss VOR dem 40149-Write liegen.
        idx_cleanup = branch["then"].index(cleanup)
        idx_40149 = next(
            i
            for i, s in enumerate(branch["then"])
            if s.get("action") == "modbus.write_register"
            and s["data"]["address"] == 40149
        )
        assert idx_cleanup < idx_40149, f"{alias}: Cleanup nach 40149"


def test_40149_werte_geklemmt():
    bp = load_blueprint()
    found = 0
    for a in bp["actions"]:
        for sub in a.get("then", []) or []:
            if (
                sub.get("action") == "modbus.write_register"
                and sub["data"]["address"] == 40149
            ):
                tmpl = str(sub["data"]["value"][1])
                assert "| min" in tmpl and "| max" in tmpl, (
                    f"{a.get('alias')}: 40149 ungeklemmt"
                )
                assert "10000" in tmpl
                found += 1
    assert found == 4


def test_tracker_und_timestamp_in_schienen_branches():
    """F2/F6: alle Schienen-Branches pflegen Tracker (CMD|<Modus>) und
    Schreibzeitpunkt, sonst falscher Stillstandsalarm im Wächter."""
    bp = load_blueprint()
    schienen = dict(KOMMANDO_BRANCHES)
    schienen["Wenn Akku Automatik"] = "Akku Automatisch"
    branches = {
        a.get("alias"): a for a in bp["actions"] if a.get("alias") in schienen
    }
    assert len(branches) == len(schienen)
    for alias, branch in branches.items():
        texts = [
            s
            for s in branch["then"]
            if s.get("action") == "input_text.set_value"
        ]
        assert texts and texts[-1]["data"]["value"].startswith("CMD|"), (
            f"{alias}: Tracker fehlt"
        )
        assert any(
            s.get("action") == "input_datetime.set_datetime" for s in branch["then"]
        ), f"{alias}: Timestamp fehlt"


def test_zweiter_stale_guard_nach_freigabe():
    """R1+S1 (Codex-Reviews 2026-07-12): nach der ~3-s-Freigabesequenz muss
    der Modus erneut geprüft werden; bei Staleness in einen Sperr-Modus muss
    VOR dem Stop ein konservatives Sperr-Set ([0,0]-Fenster + OpMod)
    geschrieben werden (verworfener Trigger bei voller Queue ließe sonst das
    offene Freigabe-Set bis zum 2-min-Tick stehen)."""
    bp = load_blueprint()
    actions = bp["actions"]
    assert str(actions[1].get("alias", "")).startswith("CmpBMS-Freigabe")
    guard2 = actions[2]
    assert str(guard2.get("alias", "")).startswith("Stale-Guard 2")
    assert "run_modus" in guard2["if"][0]["value_template"]
    # Letzter Schritt: Stop; davor der Sperr-Cleanup-Zweig.
    assert "stop" in guard2["then"][-1]
    cleanup = guard2["then"][0]
    assert str(cleanup.get("alias", "")).startswith("Sperr-Cleanup")
    writes = [
        s for s in cleanup["then"] if s.get("action") == "modbus.write_register"
    ]
    addrs = [w["data"]["address"] for w in writes]
    assert addrs == [40793, 40795, 40797, 40799, 40801, 41259]
    # Alle Fensterwerte des Cleanups sind 0 (konservativ ueber-sperrend).
    for w in writes[:5]:
        assert w["data"]["value"] == [0, 0]


def test_freigabe_bedingung_liest_tracker_zur_ausfuehrungszeit():
    """R2 (Codex-Review 2026-07-12): die Freigabe-Bedingung muss den Tracker
    zur Ausführungszeit lesen (states(snapshot_helper) im Template), nicht
    über eine beim Trigger eingefrorene Variable."""
    bp = load_blueprint()
    release = bp["actions"][1]
    cond = release["if"][0]["value_template"]
    assert "states(snapshot_helper)" in cond
    assert "needs_cmpbms_release" not in cond
