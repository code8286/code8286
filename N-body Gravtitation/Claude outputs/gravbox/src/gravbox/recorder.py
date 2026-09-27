"""Time-series diagnostics: energy, momentum and angular momentum."""

from __future__ import annotations

import csv
from collections import deque
from pathlib import Path
from typing import Deque, Dict, Optional, Tuple

FIELDS = ("time", "bodies", "kinetic", "potential", "total", "rel_drift",
          "px", "py", "pz", "lx", "ly", "lz")


class Recorder:
    """Samples conserved quantities once per frame and keeps a history.

    ``rel_drift`` is ``(E - E0) / |E0|`` where ``E0`` is re-based whenever the
    body set or the force law changes (adding bodies, merging, changing G or
    softening), because energy is only expected to be conserved between those
    events.
    """

    def __init__(self, maxlen: int = 100_000, history: int = 600) -> None:
        self.rows: Deque[Tuple[float, ...]] = deque(maxlen=maxlen)
        self.drift: Deque[float] = deque(maxlen=history)
        self.kinetic: Deque[float] = deque(maxlen=history)
        self.recording = True
        self.e0: Optional[float] = None
        self.latest: Dict[str, float] = {}

    def rebase(self) -> None:
        self.e0 = None

    def reset(self) -> None:
        self.rows.clear()
        self.drift.clear()
        self.kinetic.clear()
        self.e0 = None
        self.latest = {}

    def sample(self, system, G: float, eps: float, record: bool = True) -> Dict[str, float]:
        ke = system.kinetic_energy()
        pe = system.potential_energy(G, eps)
        total = ke + pe
        if self.e0 is None:
            self.e0 = total
        drift = (total - self.e0) / abs(self.e0) if abs(self.e0) > 1e-12 else 0.0
        p = system.momentum()
        L = system.angular_momentum()
        row = {
            "time": float(system.time), "bodies": float(system.n),
            "kinetic": ke, "potential": pe, "total": total, "rel_drift": drift,
            "px": float(p[0]), "py": float(p[1]), "pz": float(p[2]),
            "lx": float(L[0]), "ly": float(L[1]), "lz": float(L[2]),
        }
        self.latest = row
        if record:
            self.drift.append(drift)
            self.kinetic.append(ke)
            if self.recording:
                self.rows.append(tuple(row[f] for f in FIELDS))
        return row

    def export_csv(self, path: Path) -> int:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(FIELDS)
            writer.writerows(self.rows)
        return len(self.rows)
