# Physics & numerics

This document explains what the simulator actually computes and why, so the
numbers in the **DATA** tab and in exported CSVs can be trusted and interpreted.

## Model

An isolated system of `N` point masses interacting only through Newtonian
gravity. There are no external forces, so total energy, linear momentum and
angular momentum are conserved by the true dynamics. Presets are shifted into
the **centre-of-mass frame** on load (zero net position and momentum) so the
system does not drift off-screen.

Units are arbitrary but consistent: length in *world units*, time in *time
units (t.u.)*, and `G` is a free parameter (default `1.0`). Preset velocities
are computed from the current `G`, so circular orbits stay circular if you
change gravity before loading a preset.

## Force law and softening

The pairwise acceleration uses **Plummer softening**:

```
a_i = G * sum_j  m_j (r_j - r_i) / (|r_j - r_i|^2 + eps^2)^(3/2)
```

`eps` (the *softening length*) caps the force during close encounters. Without
it, two bodies passing very close produce enormous accelerations, a fixed
timestep can no longer resolve the encounter, and the integration "explodes".
Softening is the main numerical safety valve alongside the CPU watchdog.

The matching potential energy is

```
U = -G * sum_{i<j}  m_i m_j / sqrt(|r_i - r_j|^2 + eps^2)
```

and this *softened* energy is what the DATA tab reports, because it is the
quantity the integrators conserve.

The force evaluation is brute-force O(N^2), written as a few numpy matrix
operations. On a typical desktop CPU that comfortably handles a few hundred
bodies at dozens of substeps per frame.

## Integrators

| Integrator | Order | Symplectic | Force evals / step | Behaviour over long runs |
|---|---|---|---|---|
| **Euler** (explicit) | 1 | no | 1 | Energy drifts steadily; orbits spiral outward. Included for comparison. |
| **Leapfrog** (kick-drift-kick) | 2 | yes | 1 | Energy error stays bounded and oscillates. The standard choice for gravity. Default. |
| **RK4** | 4 | no | 4 | Very accurate per step, but energy slowly leaks over long integrations. |

Switch integrators live in the **PHYS** tab and watch the *Energy drift* graph
in **DATA**: Euler drifts visibly within seconds, leapfrog stays flat at the
~1e-7 level on the built-in presets with the default timestep.

## Time stepping and CPU safety

Each rendered frame advances the simulation by `substeps x dt`. Increasing
substeps speeds the simulation up without making each step less accurate;
increasing `dt` speeds it up *and* makes it less accurate.

A watchdog keeps the app responsive:

1. The physics time per frame is measured and compared with the **step budget**.
2. Over budget, the effective number of substeps is cut by 30%. Well under
   budget, it creeps back up towards the requested value.
3. A hard stop aborts a frame's physics if it takes more than 3x the budget,
   so the UI can never freeze.
4. If any body's state becomes NaN/infinite, those bodies are removed, the
   simulation pauses, and you're told to lower `dt` or raise softening.

When throttled, the simulation runs *slower in wall-clock time*, never less
accurately. The status bar and stats overlay show `THROTTLED`.

## Collisions

With **Merge on collision** enabled, overlapping bodies merge perfectly
inelastically: mass and linear momentum are conserved, kinetic energy is not.
The energy-drift baseline is re-based after every merge (and whenever bodies
are added/removed or `G`/`eps` change) because energy is only expected to be
conserved between such events.

Body radius (for drawing and collisions) is `0.5 * cbrt(mass)` world units.

## 2D and 3D

The engine is always 3D. A "2D" system simply has every `z` and `vz` equal to
zero, and gravity keeps it in the plane. **Switch to 3D** optionally adds small
random `z` offsets and `z` velocities (about 5% of the system size and the RMS
speed) so a flat system genuinely evolves in three dimensions. **Flatten to
plane** does the reverse. The 2D view is a top-down projection of whatever the
3D state is.

## Presets

| Key | Preset | What to look for |
|---|---|---|
| 1 | Figure-8 | Chenciner-Montgomery choreography: three equal masses chasing each other on one figure-eight. Softening eventually perturbs it, showing sensitivity to initial conditions. |
| 2 | 4-Body Square | Four equal masses spun at 80% of circular speed. Orderly at first, then decays into close encounters and ejections. |
| 3 | Binary Star | Two equal stars on a circular orbit: the cleanest energy-conservation check. |
| 4 | Lagrange Triangle | Equilateral three-body solution; unstable for equal masses, so it slowly breaks up. |
| 5 | Pythagorean | Burrau's problem: masses 3, 4, 5 released from rest on a 3-4-5 triangle. Famous for chaos and a final ejection. |
| 6 | Solar System | A star with seven planets on circular orbits. |
| 7 | Circumbinary | Planets orbiting a close binary (think Kepler-16). |
| 8 | Disk Cluster | 100 stars in a slowly rotating disk collapsing under their own gravity. |
| 9 | Galaxy Collision | Two rotating disks on a bound, off-centre collision course: tidal tails. |
| 0 | 3D Cluster | Roughly virialised spherical cluster with 3D velocities. |

## Exported data

`Export series CSV` writes one row per simulated frame:

| column | meaning |
|---|---|
| `time` | simulation time (t.u.) |
| `bodies` | number of bodies |
| `kinetic`, `potential`, `total` | energies (softened potential) |
| `rel_drift` | `(E - E0) / abs(E0)` since the last re-base |
| `px, py, pz` | total linear momentum |
| `lx, ly, lz` | total angular momentum about the origin |

`Export state CSV` writes the instantaneous state of every body:
`uid, mass, radius, x, y, z, vx, vy, vz, time`.

Snapshots (`Save snapshot`) are JSON files containing every body plus the
physics settings; load them with `Load latest`, `Ctrl+O` or `--load FILE`.
