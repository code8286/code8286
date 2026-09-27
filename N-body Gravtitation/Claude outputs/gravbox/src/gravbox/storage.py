"""Snapshot save/load (JSON) and state export (CSV)."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Optional

from gravbox import __version__

SNAPSHOT_FORMAT = 1


def save_snapshot(path: Path, system, sim_config: dict, label: str = "") -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "format": SNAPSHOT_FORMAT,
        "app_version": __version__,
        "label": label,
        "time": float(system.time),
        "sim": sim_config,
        "bodies": system.to_bodies(),
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1)


def load_snapshot(path: Path) -> dict:
    """Return the parsed snapshot. Raises ``ValueError`` on malformed files."""
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict) or not isinstance(data.get("bodies"), list):
        raise ValueError("not a GravBox snapshot file")
    for b in data["bodies"]:
        if not isinstance(b, dict) or not {"pos", "vel", "mass"} <= b.keys():
            raise ValueError("snapshot body is missing pos/vel/mass")
    data.setdefault("time", 0.0)
    data.setdefault("sim", {})
    data.setdefault("label", Path(path).stem)
    return data


def latest_snapshot(directory: Path) -> Optional[Path]:
    files = sorted(Path(directory).glob("*.json"), key=lambda p: p.stat().st_mtime)
    return files[-1] if files else None


def export_state_csv(path: Path, system) -> int:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    radii = system.radii()
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["uid", "mass", "radius", "x", "y", "z", "vx", "vy", "vz", "time"])
        for i in range(system.n):
            writer.writerow([int(system.uids[i]), float(system.mass[i]), float(radii[i]),
                             *system.pos[i].tolist(), *system.vel[i].tolist(), float(system.time)])
    return system.n
