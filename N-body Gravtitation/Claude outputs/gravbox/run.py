#!/usr/bin/env python3
"""Run the simulator straight from a source checkout, without installing.

    python run.py            # default preset
    python run.py --help     # all command-line options
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from gravbox.app import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
