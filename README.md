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

Interactive N-body gravity simulator for desktop and browser. Implements five numerical integrators including adaptive **RK45 (Dormand–Prince)** with PI step-size control and a **time-symmetric adaptive leapfrog** for close-encounter refinement. A numpy-vectorised **Barnes–Hut octree** (Morton linear encoding, batched matmul force kernel) runs ≈ 57× faster than the direct sum at 100k bodies with ~4 × 10⁻⁴ median force error. A live energy-drift **trust indicator** grades integration quality in real time.

The browser build offloads physics to a **Web Worker** backed by a **WebAssembly core** compiled from C (`gravcore.c`, 1.9 KB); numpy parity verified via fixture tests. No build step — deployed to GitHub Pages as-is.

**WIP:** WebGPU direct-sum backend (WGSL shader, SwiftShader-verified) targeting a `wgpu-py` / CuPy desktop path. Precision constraint established: **float32 forces + float64 state** (float32-only state degrades energy drift ~1000×). FMM vs Barnes–Hut benchmarking at 500k–1M bodies in progress.

</details>

---

<details open>
<summary><strong>🤖 MedBot+</strong> — autonomous medication-delivery robot</summary>

<br>

ESP8266-based mobile robot for medication delivery in healthcare settings. Navigation uses **RSSI log-distance path-loss ranging** combined with **MPU6050 gyro-Z heading hold** for a hill-climbing approach heuristic; medication pickup is verified via analog IR thresholding; obstacle avoidance runs an HC-SR04 on a sweep servo. Return-to-park uses IMU dead-reckoning cross-checked against RSSI. Full-stack hospital deployment vision: **React + Vite** client over a **Node.js / SQLite** multi-bot dashboard.

Production comms use **ESP-NOW** peer-to-peer ranging between ESP8266 nodes — currently substituted with phone-hotspot RSSI after a hardware fault on the second ESP. Voice prompts (DFPlayer Mini) deferred on GPIO pin budget; all cue points exercise the same state-machine timing paths via Serial log lines so the logic is testable now.

| Layer | Status |
|---|---|
| Navigation · obstacle avoidance · IR pickup · return-to-park | ✅ Implemented |
| ESP-NOW checkpoint comms (production path) | 🔧 Blocked — hardware fault |
| React / Node hospital dashboard | 🔧 In progress |
| DFPlayer voice prompts | ⏸️ Deferred — GPIO budget |

</details>

---

<details open>
<summary><strong>🚀 Active Thrust Vector Control</strong> — model-rocket closed-loop attitude control</summary>

<br>

Active TVC system for a model rocket: a **servo-actuated two-axis (pitch/yaw) motor gimbal** driven by a closed-loop PID controller. The control law is developed and tuned in a **6-DOF Python simulation** then deployed to MCU firmware on a hardware-timed interrupt loop; IMU attitude fused via complementary / lightweight Kalman filter. Three hardware phases — static tethered test fires → drone-lift free-fall drop tests → guided powered ascent with in-flight retasking and controlled descent. 3D-printed gimbal hardware (TVC_v1 STLs + gcode) exists; Phase I is current.

| Phase | Objective | State |
|---|---|---|
| I — Perfecting TVC | Static tethered burns; minimise closed-loop attitude error | 📐 Current |
| II — Dynamic Simulation | Drone-lift free-fall drops; landing-coordinate error characterisation | — |
| III — Launch & Descent | Guided ascent · in-flight retask · controlled descent to target | — |

Open decisions before hardware lock: **roll authority** (active fin tabs vs passive canted fins) and **descent propulsion architecture** (ballistic + chute vs timed landing burn). Long-term target: scale to supersonic-class vehicles.

</details>

---

<details open>
<summary><strong>📡 Morse Analyser & Encoder</strong> — C++17 audio-steganography toolkit</summary>

<br>

Self-contained C++17 toolkit — zero third-party dependencies. All numerical code (WAV I/O, FFT, Hilbert transform, zero-phase Butterworth filter, STFT, k-means, PNG/SVG output) implemented from scratch in `morse_lib/`.

The **encoder** synthesises Morse WAV audio and hides a payload in inter-gap timing (carrier-gap steganography scheme). The **analyser** inverts this: Hilbert envelope → zero-phase 20 Hz Butterworth → percentile threshold → tone-burst extraction → 3-means unit estimation → simultaneous visible Morse decode and steganographic payload recovery. Ships as a cross-platform CLI pair and a plain **Win32 GUI** joining both.

</details>

---

## 💡 In the Pipeline

<details>
<summary><strong>🔊 DigiAudx</strong> — Windows system-wide audio DSP engine</summary>

<br>

C++20 application acting as a system-wide virtual soundcard. **WASAPI loopback capture** feeds a real-time DSP chain — zero heap allocation on the audio thread — before output via `IAudioRenderClient`. Chain: 9-band IIR graphic EQ · **Linkwitz-Riley crossover timbre exciter** (harmonic generation above 4 kHz) · lookahead brickwall limiter + soft-knee compressor · **psychoacoustic bass enhancer** (sub-120 Hz upper-harmonic generation). State managed via **JUCE APVTS**; 30 FPS FFT spectrum visualiser over a lock-free FIFO on the GUI thread. Full engineering spec and module breakdown written. No code yet.

</details>

<details>
<summary><strong>🧠 Concepts queued</strong></summary>

<br>

| Project | Note |
|---|---|
| **DIY Neural Network** | From-scratch implementation — architecture TBD |
| **DIY Search Engine** | Custom indexing and retrieval pipeline — architecture TBD |
| **Ring Mouse** | Wearable ring tracking finger gestures and movement — hardware TBD |

</details>

---

## 🔬 Research

<details>
<summary><strong>🧬 hPSC Gene Regulatory Network Interface</strong> — stochastic pluripotency model</summary>

<br>

Stochastic nonlinear dynamical model of human pluripotent stem-cell fate. The OCT4–SOX2–NANOG–GATA6–PAX6 circuit is reduced to a two-axis **P / D** system (pluripotency vs differentiation) with Hill-type cooperative activation/repression and a **Chemical Langevin Equation** stochastic layer. Built and numerically validated end-to-end in GNU Octave 8.4.0 — no external packages, ~70 s runtime.

Key results: Newton–Raphson fixed-point search recovers **genuine tristability** (3 stable + 2 saddle fixed points at κ = 1.6); κ-bifurcation sweep shows tristability robust for κ ≳ 0.6 across a >4× parameter range with a pitchfork-type stability-exchange near κ ≈ 0.38 bracketed by two saddle-node annihilations — richer than the textbook single-pitchfork picture. **Waddington quasi-potential** reconstructed from a 70-trajectory CLE ensemble; Hessian curvature cross-checked via exact **Lyapunov route** (stable wells) and empirical histogram route — discrepancy attributed to finite-bin + kernel smoothing, documented explicitly.

**Next:** explicit GATA6 third axis · bursting-aware CLE (Kursawe–Galla 2025) · L1-regularised **W** from scRNA-seq + scATAC-seq · transition-path barrier heights → iPSC reprogramming first-passage times.

</details>

<details>
<summary><strong>🔥 Hybrid Wildfire Modeling</strong> — differentiable CA + GNN fire prediction</summary>

<br>

5-layer hybrid wildfire prediction system fusing USGS DEM terrain, LANDFIRE fuel models, NOAA NDFD weather, and NASA FIRMS satellite hotspots. A **differentiable cellular automaton** (PyTorchFire, GPU) implements the Rothermel spread model with Huygens elliptical anisotropy; a lightweight **Graph Attention Network** (~30–50k params) runs in parallel on an adaptive quad-tree mesh (250 m → 60 m near fire front, 60–70% memory saving vs uniform grid) to output per-node spot-fire probability, spread-speed correction, and direction bias — recovering **~75–80% spot-fire recall vs ~40% for CA alone**. **Real-time gradient-descent calibration** fits Rothermel R₀ to satellite fire boundaries (IoU + Hausdorff loss) in under 2 min on an A100.

**2020 Diablo Wind Fire benchmark:** hybrid CA+GNN+calibration reaches **0.81 IoU at 6 h in 35 ms/step** vs 0.68 IoU at 850 ms/step for CPU CA. Full specification complete; 16-week implementation roadmap ready.

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
- Can physics-grounded simulation plus a light learned correction beat a pure neural model on speed, accuracy, and out-of-distribution generalisation simultaneously?
- How can a control system move from a simulation to a test bench without skipping the hard engineering questions in between?

I also keep an **aerospace ideas notebook** — problems in autonomy, manufacturing, metrology, and flight systems. Some ideas are seeds, not promises; the work is figuring out which ones deserve a prototype.

---

## 🛠️ Things I work with

`Python` · `C/C++` · `JavaScript` · `Numerical simulation` · `Embedded systems (ESP8266/ESP32)` · `Robotics` · `DSP` · `Control systems` · `WebAssembly` · `GNU Octave / MATLAB` · `PyTorch · GNNs` · `React + Node`

---

### Find me around GitHub

[Repositories](https://github.com/code8286?tab=repositories) · [GravBox source](https://github.com/code8286/gravbox) · 

<p align="center"><sub>Curiosity in, Explosives out. Repeat.</sub></p>
