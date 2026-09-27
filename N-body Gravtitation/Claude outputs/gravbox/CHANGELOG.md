# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-09-24

### Changed
- Project renamed to **GravBox** (package, CLI command, data folder, and all branding).
- Desktop and web UI restyled to a shared design: monochrome glass panels, pill tabs, starfield, glowing bodies.
- Added a browser version (`web/`) with a GitHub Pages deploy workflow.

### Added
- Vectorised numpy N-body engine with Plummer softening.
- Euler, leapfrog (symplectic, default) and RK4 integrators.
- Ten presets, including figure-8, Pythagorean three-body and galaxy collision.
- Tabbed control panel: SIM, PHYS, BODIES, VIEW, DATA, HELP.
- Persistent trails that keep their full history at bounded memory.
- OpenGL 3D view with orbit camera and one-click 2D to 3D conversion.
- Fullscreen mode (F11 / Alt+Enter) at native desktop resolution.
- DPI-aware, aspect-correct window sizing on Windows, macOS and Linux.
- CPU watchdog that throttles substeps to stay within a per-frame budget.
- Live energy / momentum / angular momentum diagnostics with graphs.
- CSV export (time series and state), JSON snapshots, PNG screenshots.
- Mouse spawning with click-and-drag velocity aiming.
- Settings persisted between sessions.
- Test suite, GitHub Actions CI and a PyInstaller build script.
