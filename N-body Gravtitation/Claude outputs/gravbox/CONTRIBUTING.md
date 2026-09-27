# Contributing

Thanks for your interest in improving GravBox!

## Development setup

```bash
git clone https://github.com/YOUR_USERNAME/gravbox.git
cd gravbox
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
```

## Before opening a pull request

```bash
ruff check src tests     # lint
pytest                   # tests (no display needed)
```

CI runs both on Windows, macOS and Linux.

## Where things live

- `physics.py`, `presets.py`, `trails.py`, `recorder.py`, `storage.py`, `config.py`
  and `render/camera.py` are pure Python + numpy and are fully unit-tested.
  Keep them free of pygame imports.
- `ui/` and `render/renderer2d.py` / `renderer3d.py` contain drawing code.
- `app.py` wires everything together (events, actions, main loop).

## Adding a preset

1. Write a builder in `src/gravbox/presets.py` with the signature
   `def my_preset(G: float, rng: random.Random) -> list[dict]`.
2. Register it in the `PRESETS` list with a key, label and one-line description.
3. `tests/test_presets.py` automatically checks it is valid and conserves energy.

## Style

- Follow the existing code style (enforced by ruff, 120-char lines).
- Prefer small, well-named functions and docstrings that explain *why*.
- Add or update tests for behaviour changes.
