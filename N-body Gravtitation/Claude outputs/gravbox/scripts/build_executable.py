#!/usr/bin/env python3
"""Build a standalone, double-clickable executable with PyInstaller.

    pip install -e ".[build]"
    python scripts/build_executable.py

The result is written to ``dist/GravBox/`` (a folder you can zip and
share). Pass ``--onefile`` for a single executable (slower to start).
"""

from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--onefile", action="store_true", help="bundle into a single executable")
    args = parser.parse_args()

    if importlib.util.find_spec("PyInstaller") is None:
        print("PyInstaller is not installed. Run:  pip install pyinstaller", file=sys.stderr)
        return 1

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean", "--windowed",
        "--name", "GravBox",
        "--paths", str(ROOT / "src"),
        "--collect-submodules", "gravbox",
    ]
    if importlib.util.find_spec("OpenGL") is not None:
        # PyOpenGL loads its platform back-end dynamically.
        cmd += ["--collect-submodules", "OpenGL"]
    if args.onefile:
        cmd.append("--onefile")
    cmd.append(str(ROOT / "run.py"))

    print(" ".join(cmd))
    return subprocess.call(cmd, cwd=ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
