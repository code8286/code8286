import csv
import json

import pytest

from gravbox.config import Settings
from gravbox.physics import NBodySystem
from gravbox.recorder import FIELDS, Recorder
from gravbox.storage import export_state_csv, latest_snapshot, load_snapshot, save_snapshot


def test_settings_round_trip(tmp_path):
    s = Settings()
    s.sim.gravity = 3.5
    s.view.show_grid = False
    s.window.fullscreen = True
    path = tmp_path / "settings.json"
    s.save(path)
    loaded = Settings.load(path)
    assert loaded.sim.gravity == 3.5
    assert loaded.view.show_grid is False
    assert loaded.window.fullscreen is True


def test_settings_tolerate_garbage(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"sim": {"gravity": "abc", "substeps": 10_000, "integrator": "magic",
                                        "unknown": 1}, "view": "nope"}))
    s = Settings.load(path)
    assert s.sim.gravity == Settings().sim.gravity
    assert s.sim.substeps == 256
    assert s.sim.integrator == "leapfrog"


def test_missing_or_corrupt_settings_fall_back(tmp_path):
    assert Settings.load(tmp_path / "missing.json") == Settings()
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    assert Settings.load(bad) == Settings()


def make_system():
    s = NBodySystem()
    s.add((1, 2, 3), (4, 5, 6), 7.0, (1, 2, 3))
    s.add((-1, 0, 0), (0, 1, 0), 2.0, (9, 9, 9))
    s.time = 12.5
    return s


def test_snapshot_round_trip(tmp_path):
    s = make_system()
    path = tmp_path / "saves" / "a.json"
    save_snapshot(path, s, Settings().to_dict()["sim"], "demo")
    data = load_snapshot(path)
    assert data["label"] == "demo"
    assert data["time"] == 12.5
    t = NBodySystem()
    t.load(data["bodies"], data["time"])
    assert t.n == 2 and t.colors[0] == (1, 2, 3)
    assert latest_snapshot(tmp_path / "saves") == path


def test_bad_snapshot_rejected(tmp_path):
    path = tmp_path / "x.json"
    path.write_text(json.dumps({"bodies": [{"pos": [0, 0, 0]}]}))
    with pytest.raises(ValueError):
        load_snapshot(path)


def test_state_csv(tmp_path):
    path = tmp_path / "state.csv"
    assert export_state_csv(path, make_system()) == 2
    rows = list(csv.reader(path.open()))
    assert rows[0][:4] == ["uid", "mass", "radius", "x"]
    assert len(rows) == 3


def test_recorder_drift_and_export(tmp_path):
    s = make_system()
    rec = Recorder()
    first = rec.sample(s, 1.0, 1.0)
    assert first["rel_drift"] == 0.0
    s.vel *= 1.1
    second = rec.sample(s, 1.0, 1.0)
    assert second["rel_drift"] != 0.0
    rec.rebase()
    assert rec.sample(s, 1.0, 1.0)["rel_drift"] == 0.0
    path = tmp_path / "series.csv"
    assert rec.export_csv(path) == 3
    rows = list(csv.reader(path.open()))
    assert tuple(rows[0]) == FIELDS and len(rows) == 4


def test_recorder_respects_recording_flag():
    rec = Recorder()
    rec.recording = False
    rec.sample(make_system(), 1.0, 1.0)
    assert len(rec.rows) == 0 and len(rec.drift) == 1
