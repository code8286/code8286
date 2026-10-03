# Hiii I'm Soumo 👋

### I build things that move, listen, navigate, and occasionally blow up :3

I'm an undergraduate engineering student exploring **aerospace, analog and digital electronics, robotics, audio, signal processing, and scientific software**. This is my project workbench — some things are running, some are being prototyped, and some are still ambitious notes waiting to become hardware or code.

<p align="center">
  <a href="https://github.com/code8286?tab=repositories"><img alt="Explore my repositories" src="https://img.shields.io/badge/_Explore-Projects-2457A7?style=for-the-badge"></a>
  <a href="https://github.com/code8286/gravbox"><img alt="GravBox" src="https://img.shields.io/badge/_Play-GravBox-147D64?style=for-the-badge"></a>
  <a href="https://code8286.github.io/GravBox/"><img alt="Try GravBox online" src="https://img.shields.io/badge/_Launch-Web_Demo-C14F27?style=for-the-badge"></a>
</p>

---

## 🗂️ Quick Reference

| # | Project | Domain | Stack | Status |
|---|---|---|---|---|
| 1 | [**GravBox**](https://github.com/code8286/gravbox) | Computational physics · Web | Python · JS · WASM | ✅ v1.1.0 shipped |
| 2 | [**MedBot+**](https://github.com/akshaykumar-2008/MedBot-Plus) | Embedded robotics · Full-stack | ESP8266 · React · Node | ⚠️ Phase 2 bench testing |
| 3 | **Active Thrust Vector Control** | Aerospace · Control systems | Python · C++ firmware | 📐 Design & planning |
| 4 | [**Morse Analyser**](https://github.com/code8286/morse_analyser.git) | DSP · Steganography | C++17 · Win32 | ✅ Built & functional |
| 5 | **DigiAudx** | Audio DSP · Windows systems | C++20 · JUCE · WASAPI | 💡 Spec written, no code |
| 6 | **Adaptive Noise Cancellation** | Speech enhancement · Edge AI | PyTorch · TensorRT | 📄 Research concept |
| 7 | **Space Debris Tracking** | Aerospace · ML | Sensor fusion · ML | 📄 Research concept |

---

## 🔬 Active Projects

<details open>
<summary><strong>🪐 GravBox</strong> — N-body gravitational simulator</summary>

<br>

> Interactive desktop sandbox and browser demo for the gravitational N-body problem — from 2-body Keplerian orbits to 100,000-body galaxy collisions.

**Integrators**

| Name | Type | Notes |
|---|---|---|
| Euler | Fixed-step | Baseline |
| Leapfrog | Symplectic fixed-step | Default — energy-conservative |
| RK4 | Fixed-step 4th-order | — |
| RK45 (Dormand–Prince) | Adaptive, error-controlled | PI step-size control, dense output |
| Adaptive leapfrog | Time-symmetric | Close-encounter auto-refinement |

**Barnes–Hut octree** (optional, toggled per preset)

| N (bodies) | Direct sum | Barnes–Hut (θ = 0.5) | Speedup | Median force error |
|---|---|---|---|---|
| 100 000 | ~105 s | ~1.84 s | **≈ 57×** | ~4 × 10⁻⁴ |

**Web build** — `web/`, vanilla JS, no build step, deployed to GitHub Pages

```
Browser main thread  (rendering, UI)
       │
  Web Worker  ←──────────────────────────────────┐
       │                                          │
  GravCoreWasm  (gravcore.c → .wasm, 1.9 KB)   GravCoreJS  (JS fallback)
  numpy parity verified via fixture tests
```

**WIP — GPU acceleration** (`WIP/gpu-acceleration/`)
- WebGPU backend (WGSL direct-sum shader, verified on SwiftShader) → `wgpu-py` / CuPy desktop path
- Precision rule locked: **float32 forces + float64 state** (float32-only degrades energy drift ~1000×)
- Neural force surrogates only beneficial past ~10⁶ bodies; not planned before then
- FMM vs Barnes–Hut at 500k–1M bodies benchmark in progress

</details>

---

<details open>
<summary><strong>🤖 MedBot+</strong> — autonomous medication-delivery robot</summary>

<br>

> ESP8266-based mobile robot that navigates autonomously to a patient, verifies medication pickup via IR sensing, avoids obstacles, and returns to a parking position. Hospital deployment vision: a React/Node central dashboard managing a fleet.

**Subsystem status**

| Subsystem | Implementation | State |
|---|---|---|
| Motor control | 12V DC H-bridge; PWM-on-direction-pins | ✅ |
| Navigation / approach | RSSI hill-climbing heuristic + MPU6050 heading hold | ✅ |
| Obstacle avoidance | HC-SR04 on sweep servo; stop-and-turn | ✅ |
| IMU / heading | MPU6050 raw I2C; gyro-Z integration | ✅ (drifts — prototype-grade) |
| Medicine pickup detect | Analog IR; Dark/Bright threshold | ✅ |
| Return-to-park | IMU dead-reckoning cross-checked against RSSI | ✅ |
| Checkpoint comms | ESP-NOW (production target) | 🔧 Blocked — USB-serial chip dead |
| Checkpoint comms | Phone hotspot RSSI substitute | ⚠️ Current active test |
| Voice prompts | DFPlayer Mini + speaker | ⏸️ Deferred — GPIO pin budget |
| Web dashboard | React + Vite client · Node/SQLite server | 🔧 In progress |

**Communication history**
```
Production target:
  Bot ESP8266  ←── ESP-NOW ──→  Checkpoint ESP8266
                                (log-distance path-loss RSSI ranging)

Active substitute (second ESP8266 USB-serial unrecoverable):
  Bot ESP8266  ←── Wi-Fi RSSI ──→  Phone hotspot
               Same path-loss model · single-checkpoint only · not production
```

**Next:** replace failed ESP8266 · PCF8574 I2C GPIO expander or migrate to ESP32 for DFPlayer · complete multi-bot hospital dashboard

</details>

---

<details open>
<summary><strong>🚀 Active Thrust Vector Control</strong> — model-rocket closed-loop attitude control</summary>

<br>

> Servo-actuated two-axis (pitch/yaw) motor gimbal driven by a closed-loop PID controller, prototyped and tuned in Python, then deployed to MCU firmware. Three progressive hardware phases.

**Phase roadmap**

```
╔══════════════════════════════════════════════════════════════════════╗
║  PHASE I — Perfecting TVC                              [CURRENT]    ║
╠══════════════════════════════════════════════════════════════════════╣
║  Build:    cross/yoke gimbal on low-friction bearings               ║
║  Sense:    MPU6050 → complementary / lightweight Kalman filter      ║
║  Control:  PID tuned in Python → MCU hardware-timed ISR firmware    ║
║  Validate: static tethered motor burns; minimise attitude error     ║
╠══════════════════════════════════════════════════════════════════════╣
║  PHASE II — Dynamic Simulation                                      ║
╠══════════════════════════════════════════════════════════════════════╣
║  Test:     drone-lift free-fall drop tests (inert mass first)       ║
║  Detect:   freefall via accelerometer near-zero net-accel debounce  ║
║  Sim:      6-DOF Python model pre-validates gains before drops      ║
║  Validate: landing-coordinate error across repeated trials          ║
╠══════════════════════════════════════════════════════════════════════╣
║  PHASE III — Launch & Controlled Descent                            ║
╠══════════════════════════════════════════════════════════════════════╣
║  Fly:      guided powered ascent on pre-set roll/pitch/yaw profile  ║
║  ReTask:   in-flight command via two-way telemetry link             ║
║  Land:     controlled descent to target landing zone                ║
║  Extend:   altitude envelope + telemetry/science payloads           ║
╚══════════════════════════════════════════════════════════════════════╝
```

**Open architectural decisions** — must be locked before Phase I hardware is finalised

| Decision | Option A | Option B |
|---|---|---|
| Roll authority | Servo-actuated fin tabs (active) | Canted fins (passive damping) |
| Descent propulsion | TVC-guided ballistic + parachute | Timed landing burn (suicide burn) |
| Dev surrogate | Throttleable hybrid / EDF / cold-gas | — |

**Long-term:** scale to supersonic-class vehicles · higher-bandwidth control surfaces · larger payload capacity

</details>

---

<details open>
<summary><strong>📡 Morse Analyser & Encoder</strong> — C++17 audio-steganography toolkit</summary>

<br>

> Self-contained C++17 toolkit with zero third-party dependencies. Encodes text as Morse audio and hides a steganographic payload in inter-gap timing. Analyses a WAV file to decode both the visible Morse and the hidden carrier-gap payload.

**Analyser pipeline**
```
WAV input  (PCM 8/16/24/32-bit or float 32/64-bit; multi-channel → mono)
    │
    ▼
Hilbert envelope  →  20 Hz zero-phase Butterworth low-pass
    │
    ▼
Percentile threshold  →  tone-burst segmentation
    │
    ├──► Visible Morse decode  (dot/dash timing → ASCII)
    └──► Inter-gap timing  →  3-means unit estimation
              └──► Carrier-gap steganographic payload  (normal + reversed)
                         └──► CSV · SVG envelope plot · PNG spectrogram
```

| Binary | Role | Platform |
|---|---|---|
| `morse-encoder` | Text → Morse WAV; embeds payload in inter-gap timing | Cross-platform |
| `morse-analyser` | Decodes visible Morse + hidden payload | Cross-platform |
| `morse-gui` | Win32 GUI joining both tabs | Windows |

All DSP (WAV I/O, FFT, Hilbert, Butterworth, STFT, k-means, PNG/SVG) lives in `morse_lib/`. Original Python prototype in `origin/`.

</details>

---

## 💡 In the Pipeline

<details>
<summary><strong>🔊 DigiAudx</strong> — Windows system-wide audio DSP engine</summary>

<br>

> C++20 application acting as a system-wide virtual soundcard: WASAPI loopback capture of the default render endpoint, a real-time DSP chain, and near-zero-latency passthrough to the physical output device.

**Signal chain**
```
System audio  (default Windows render endpoint)
    │
WASAPI Loopback Capture  (IAudioClient + IAudioCaptureClient)
    │
Lock-free ring buffer  (std::atomic / JUCE AbstractFifo)
    │
DSP Engine  [audio thread — zero heap allocation on hot path]
    ├── 9-band Graphic EQ          juce::dsp::IIR::Filter
    ├── Timbre Exciter             Linkwitz-Riley crossover → harmonic generation above 4 kHz
    ├── Volume Maximiser           Lookahead brickwall limiter + soft-knee compressor
    └── Psychoacoustic Bass Enh.   Sub-120 Hz isolation → upper harmonic generation
    │
IAudioRenderClient  (physical hardware endpoint)
    │
GUI thread  (JUCE APVTS · power toggle · vertical sliders · 30 FPS FFT visualiser)
```

**Status:** full engineering spec and module breakdown complete · no code yet

</details>

<details>
<summary><strong>🧠 Upcoming — concepts queued</strong></summary>

<br>

| Project | Description |
|---|---|
| **DIY Neural Network** | From-scratch implementation — architecture TBD |
| **DIY Search Engine** | Custom indexing and retrieval pipeline — architecture TBD |
| **Ring Mouse** | Wearable ring device for finger-gesture and movement tracking — hardware TBD |

</details>

---

## 🔬 Research

<details>
<summary><strong>🧬 hPSC Gene Regulatory Network Interface</strong> — stochastic pluripotency model</summary>

<br>

> Stochastic nonlinear dynamical model of human pluripotent stem-cell fate. Two-axis reduction of the OCT4–SOX2–NANOG–GATA6–PAX6 circuit with Hill-type cooperative regulation, a Chemical Langevin Equation ensemble, Newton–Raphson fixed-point search, bifurcation sweeps, and Waddington quasi-potential reconstruction.

**State-space reduction**
```
Full 5-node circuit:  OCT4 – SOX2 – NANOG – GATA6 – PAX6
            ↓  (deliberate dimensionality reduction)
  P  — pluripotency axis    (OCT4 / SOX2 / NANOG cluster)
  D  — differentiation axis (GATA6 / PAX6-type lineage repressors)

  dP/dt = aP · H⁺(P) · H⁻(κD)  −  gP·P  +  bP
  dD/dt = aD · H⁺(D) · H⁻(κP)  −  gD·D  +  bD
```

**Validated results** — GNU Octave 8.4.0, ~70 s runtime, no external packages

| Module | Result |
|---|---|
| Fixed-point search | 5 fixed points: **3 stable** (pluripotent · differentiated · uncommitted) + **2 saddle** |
| κ-bifurcation sweep | Tristability robust for κ ≳ 0.6 to 2.6; pitchfork-type exchange at κ ≈ 0.38 bracketed by two saddle-node annihilations |
| CLE stochastic ensemble | 70 trajectories (5 seeds × 14 replicates · 6 000 Euler–Maruyama steps) |
| Waddington quasi-potential | U ∈ [0, 10.39]; three deep basins confirmed at stable fixed points |
| Hessian cross-check | Lyapunov exact (wells) vs empirical histogram — qualitative agreement; magnitude discrepancy documented and attributed to finite-bin + kernel smoothing |

**Computational hierarchy**
```
Level 0  Boolean / multistate topology check
Level 1  Deterministic ODE — parameter screening         ✅ implemented
Level 2  Chemical Langevin (CLE) — stochastic ensemble   ✅ implemented
Level 3  Promoter ON/OFF bursting model
Level 4  Gillespie SSA / tau-leaping (low copy-number)
Level 5  Population model (division · clonal selection)
```

**Next:** explicit GATA6 third axis · bursting-aware CLE (Kursawe–Galla 2025) · L1-regularised W from single-cell multiomics · transition-path barrier heights → iPSC reprogramming first-passage times

</details>

<details>
<summary><strong>🔥 Hybrid Wildfire Modeling</strong> — differentiable CA + GNN fire prediction</summary>

<br>

> 5-layer hybrid system combining physics-based differentiable cellular automata (GPU-accelerated via PyTorchFire) with a graph neural network for spot-fire and spread corrections, real-time gradient-descent calibration against satellite observations, and an operational decision-support output layer.

**5-layer architecture**
```
Layer 1 — Input Fusion
    USGS DEM (30 m) · LANDFIRE fuel (30–240 m) · NOAA NDFD weather · NASA FIRMS hotspots
        ↓
Layer 2 — Adaptive Quad-Tree Mesh + GNN Graph
    250 m (base)  →  125 m (transition)  →  60 m (fire front)
    60–70% memory saving vs uniform grid · 5k–50k nodes · 64-dim features
        ↓
Layer 3 — Dual-Path Propagation
    ┌─────────────────────────────────────────────────────────────────┐
    │ Path A: Differentiable CA (PyTorchFire)                        │
    │   Rothermel R₀ · wind φ_w · slope φ_s · Huygens ellipse       │
    │   16–22 ms/step (A100) · 30–40 ms/step (RTX 4090)             │
    └─────────────────────────────────────────────────────────────────┘
    ┌─────────────────────────────────────────────────────────────────┐
    │ Path B: SpottingRefinementGNN (GAT · ~30–50k params)           │
    │   spot_fire_prob · spread_speed_factor · direction_bias ±30°   │
    │   Spot-fire recall: ~40% (CA alone) → ~75–80% (CA+GNN)        │
    └─────────────────────────────────────────────────────────────────┘
        ↓
Layer 4 — Real-Time Calibration
    Gradient descent on R₀ · Loss: IoU + Hausdorff · < 2 min on A100
        ↓
Layer 5 — Decision Support
    Burn-probability maps · Containment-time estimates · WUI risk · Evacuation zones
```

**2020 Diablo Wind Fire benchmark**

| Configuration | ms/step | IoU (6 h) | Memory |
|---|---|---|---|
| Pure CPU CA | 850 | 0.68 | 8.2 GB |
| PyTorchFire GPU | 22 | 0.72 | 2.1 GB |
| Hybrid CA + GNN | 28 | 0.78 | 2.4 GB |
| Hybrid + calibration | 35 | **0.81** | 2.1 GB |

**Status:** full specification complete · 16-week implementation roadmap ready

</details>

<details>
<summary><strong>📐 Unified Linear Network Theorem</strong></summary>

<br>

Open theoretical question — notes only, no implementation yet.

</details>

---

## 🛰️ What drives all of this

- How do you keep a numerical simulation both fast and honest about its errors?
- Can a small robot navigate using imperfect sensors and still explain its internal state?
- When does a stochastic model of a biological network stop being a diagram and start generating real predictions?
- Can physics-grounded simulation plus a light learned correction beat a pure neural model on speed, accuracy, and out-of-distribution generalization simultaneously?
- How can a control system move from a simulation to a test bench without skipping the hard engineering questions between?

I also keep an **aerospace ideas notebook** — problems in autonomy, manufacturing, metrology, and flight systems. Some ideas are seeds, not promises; the work is figuring out which ones deserve a prototype.

---

## 🛠️ Things I work with

`Python` · `C/C++` · `JavaScript` · `Numerical simulation` · `Embedded systems (ESP8266/ESP32)` · `Robotics` · `DSP` · `Control systems` · `WebAssembly` · `GNU Octave / MATLAB` · `PyTorch · GNNs` · `React + Node`

---

### Find me around GitHub

[Repositories](https://github.com/code8286?tab=repositories) · [GravBox source](https://github.com/code8286/gravbox) · 

<p align="center"><sub>Curiosity in, Explosives out. Repeat.</sub></p>