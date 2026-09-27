"""Allow ``python -m gravbox``."""

from gravbox.app import main

if __name__ == "__main__":
    raise SystemExit(main())
