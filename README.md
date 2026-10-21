# Hiii I'm Soumo 👋

### Navigating through life with neurodivergence

Undergraduate engineering victim exploring **aerospace, analog and digital electronics, robotics, audio, signal processing, and scientific software**. This is my project workbench — some things are running, some are being prototyped, and some are still ambitious notes waiting to become hardware or code.

<p align="center">
  <a href="https://github.com/code8286?tab=repositories"><img alt="Explore my repositories" src="https://img.shields.io/badge/_Explore-Projects-2457A7?style=for-the-badge"></a>
  <a href="https://github.com/code8286/gravbox"><img alt="GravBox" src="https://img.shields.io/badge/_Play-GravBox-147D64?style=for-the-badge"></a>
  <a href="https://code8286.github.io/GravBox/"><img alt="Try GravBox online" src="https://img.shields.io/badge/_Launch-Web_Demo-C14F27?style=for-the-badge"></a>
</p>

---

## 🗂️ Quick Reference

| #   | Project                                                              | Domain                                     | Stack                           | Status                                         |
| --- | -------------------------------------------------------------------- | ------------------------------------------ | ------------------------------- | ---------------------------------------------- |
| 1   | [**GravBox**](https://github.com/code8286/gravbox)                   | Computational physics · Web · Applied Math | Python · JS · WASM              | ✅ v1.1.0 shipped + 🔬 Active Research          |
| 2   | [**F.R.I.D.A.Y.**](https://github.com/code8286/F.R.I.D.A.Y..git)     | Desktop AI · Security & Agent Core         | Python 3.10+ · asyncio · SQLite | 🔧 Tranches 5–6 built, not versioned           |
| 3   | [**MedBot+**](https://github.com/akshaykumar-2008/MedBot-Plus)       | Embedded robotics · Full-stack             | ESP8266 · React · Node          | ⚠️ Phase 2 bench testing                       |
| 4   | **Active Thrust Vector Control**                                     | Aerospace · Control systems                | Python · C++ firmware           | 📐 Design & planning                           |
| 5   | [**Morse Analyser**](https://github.com/code8286/morse_analyser.git) | DSP · Steganography                        | C++17 · Win32                   | ✅ Built & functional                           |
| 6   | **DigiAudx**                                                         | Audio DSP · Windows systems                | C++20 · JUCE · WASAPI           | 🔧 Beta version implementation                 |
| 7   | [**GNNs in Neural Cellular Automata**](https://github.com/code8286/GPU_NCA_proofer.git)                                 | ML · GNNs · Language Model Initialization  | Python · PyTorch · GPU          | 🔬 v4 GPU done; v5–v9 CPU diagnostics complete |
| 8   | **Space Debris Tracking**                                            | Aerospace · ML                             | Sensor fusion · ML              | 📄 Research concept                            |
| 9   | **MPC Drone**                                                        | Aerospace · Control systems                | MATLAB · Simulink               | 🔧 Simulation prototype                        |

---

## 🔬 Active Projects

<details open>
<summary><strong>🪐 GravBox</strong> — N-body gravitational simulator & numerical laboratory</summary>

<br>

Interactive N-body gravity simulator for desktop and browser. Implements five numerical integrators including adaptive **RK45 (Dormand–Prince)** with PI step-size control and a **time-symmetric adaptive leapfrog** for close-encounter refinement. A numpy-vectorised **Barnes–Hut octree** (Morton linear encoding, batched matmul force kernel) runs ≈ 57× faster than the direct sum at 100k bodies with ~4 × 10⁻⁴ median force error. A live energy-drift **trust indicator** grades integration quality in real time.

The browser build offloads physics to a **Web Worker** backed by a **WebAssembly core** compiled from C (`gravcore.c`, 1.9 KB); numpy parity verified via fixture tests. No build step — deployed to GitHub Pages as-is.

**Dual Role:** GravBox now operates as both a shipping application and an active **Applied Mathematics research topic** — studying computational integrators and numerical approximation methods that leak less energy over extended time horizons (see [Research](#-research)).

**WIP:** WebGPU direct-sum backend (WGSL shader, SwiftShader-verified) targeting a `wgpu-py` / CuPy desktop path. Precision constraint established: **float32 forces + float64 state** (float32-only state degrades energy drift ~1000×). FMM vs Barnes–Hut benchmarking at 500k–1M bodies in progress.

**TreePM prototype (Oct 2026):** Full 72-measurement 500k–1M validation campaign completed — **production no-go**. 45/72 pass accuracy, 46 qualify for timing; all five eligible sphere matched comparisons fail the twofold speed target (TreePM 9.8–19.4× slower than BH). All 18 disk BH settings fail force accuracy; no matched disk comparison exists. Conditional application-adapter design delivered; no production backend enabled. See `Projects/N-body Gravitation/gravbox/WIP/treepm-prototype/COMPLETION_STATUS.md` and `FINAL_VALIDATION_ASSESSMENT.md`.

</details>

---

<details open>
<summary><strong>🛡️ F.R.I.D.A.Y.</strong> — standalone desktop assistant & security-first agent core</summary>

<br>

A standalone, always-on desktop assistant with full host access and a security model enforced strictly in code rather than system prompts. Built with **zero third-party runtime dependencies** in the core package (optional OS `keyring` for secret storage).

**Released: v0.4.0, Tranches 1–4** — headless core, security engine, persistent memory, model provider & CLI, local tool suite, voice activation, and the full desktop UI. Tranches 5 and 6 are built but not yet versioned (would be v0.6.0).

**Shipped (Tranches 1–4):**
- **Headless Core:** `FridayCore` asyncio daemon with SQLite (WAL mode) storage, schema migrations, event bus, kill switch, and an agent loop with budget limits and turn-boundary history repair.
- **Security Engine:** Risk tiers **T0 to T3**, multi-turn taint tracking with data envelopes, confirmation broker (single-use approvals bound to SHA-256 of exact tool + args, 60 s TTL), filesystem and SSRF access rules, hash-chained tamper-evident audit log.
- **Guarded Memory:** Long-term SQLite FTS memory, auto-extraction from clean turns only, rolling summaries for context truncation, cross-session restoration.
- **Model Provider & CLI:** `FridayProvider` with OpenAI-compatible codec verified against local OmniRoute gateway, offline echo provider, and full `friday` CLI (`run`, `init`, `set-secret`, `check-provider`, `verify-audit`, `memory`, and more).
- **Local Tools:** Tasks, notes, reminders/alarms (persistent scheduler), filesystem with undo journal and trash, shell tool, web fetcher pinned against SSRF.
- **Voice (optional):** Double-clap detector, "FRIDAY wake up" phrase (Vosk), VAD, local STT (faster-whisper), spoken replies (ElevenLabs or system voice). Half-duplex with barge-in.
- **Desktop UI:** PySide6/QML frontpage — HUD ring, eight live tiles, console with tool-activity feed and approval dock, Notes/Memories/Settings panels, kill-switch button, system-tray icon.
- **Test Suite:** 751 unit tests, stdlib only, clean across Python 3.10–3.13.

```
Tranche Roadmap:
  [✅] Tranche 1: Headless core, security engine, persistent memory, model provider & CLI
  [✅] Tranche 2: Local tools (tasks, notes, alarms, filesystem, shell, web)
  [✅] Tranche 3: Sensors & voice activation (double clap, "FRIDAY wake up", STT, TTS)
  [✅] Tranche 4: Desktop UI (PySide6 HUD, control box, approvals dock, tray)
  [🔧] Tranche 5: Integrations (Google Calendar, RSS News, GitHub) — built, not released
       + Telegram bot dropped; replaced by Android companion channel
  [🔧] Tranche 6: Native packaging (launcher, OS autostart, watchdog) + Android app — built, not released
       + Phone channel (WebSocket, TLS 1.3, pairing, biometric approvals)
       + Android app (Kotlin + Compose, Android 12+) — protocol tested; Compose UI not compiled yet
```

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

## 🔧 Beta Implementation

<details open>
<summary><strong>🔊 DigiAudx</strong> — Windows system-wide audio DSP engine</summary>

<br>

C++20 application acting as a system-wide virtual soundcard. **WASAPI loopback capture** feeds a real-time DSP chain — zero heap allocation on the audio thread — before output via `IAudioRenderClient`. Chain: 9-band parametric IIR graphic EQ · **Linkwitz-Riley crossover timbre exciter** (harmonic generation above 4 kHz) · lookahead brickwall limiter + soft-knee compressor · **psychoacoustic bass enhancer** (sub-120 Hz upper-harmonic generation). State managed via **JUCE APVTS**; 30 FPS FFT spectrum visualiser over a lock-free FIFO on the GUI thread.

**Beta implementation — what's working:** JUCE desktop application with dark responsive control surface, endpoint discovery, event-driven WASAPI loopback capture and render for matching stereo float endpoints, nine-band parametric EQ, high-frequency exciter, psychoacoustic bass enhancement, stereo width, gain, lookahead limiting, persistent power and EQ parameters, lock-free audio sample FIFO feeding a 30 FPS spectrum view, DSP smoke test, and Windows CI. Full engineering spec and module breakdown written.

**Audio routing:** WASAPI loopback captures the mix already playing through a render endpoint — it cannot intercept and replace that endpoint's output. A virtual audio device (separate Windows driver project) is required to route arbitrary app audio through the DSP chain; the scaffold deliberately rejects selecting the same endpoint for input and output.

</details>

<details>
<summary><strong>🚁 MPC Drone</strong> — quadrotor 6-DOF simulation & cascaded PD controller prototype</summary>

<br>

MATLAB quadrotor simulation for control-law development. 12-state 6-DOF model (position, velocity, Euler angles, body rates) integrated via ODE45. A **cascaded PD controller** handles outer-loop position (desired thrust + roll/pitch commands) and inner-loop attitude (body torques), with a full rotation matrix R_IB and Euler-angle-rate kinematics (W matrix). Simulink `multirotor` object configured in parallel with matching mass (1.2 kg), inertia, and drag coefficients.

**Next:** Replace cascaded PD with proper MPC; add actuator dynamics and rotor speed limits; validate against hardware.

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

<details open>
<summary><strong>🪐 Energy-Leaking Limitations in Computational N-Body Integrators & Training Methods</strong></summary>

<br>

**Domain:** Applied Mathematics · Computational Physics · Scientific ML

Investigation into where and why discrete N-body algorithms lose energy conservation over time, and the design of integrators and surrogate training methods that minimise that leakage:
- **Symplectic vs. Adaptive Formulations:** Why standard adaptive time-stepping (e.g. Dormand–Prince RK45) breaks symplecticity and introduces secular energy dissipation; time-symmetric adaptive Leapfrog as a conservative alternative.
- **Precision Cliff:** Empirical proof that `float32` forces + `float64` state preserves symplectic energy envelopes near-identically to full `float64`, whereas `float32`-only state degrades energy drift by ~1000×.
- **Spatial Truncation Asymmetry:** Non-conservative force errors and momentum injection in Barnes–Hut octrees (θ acceptance) vs. symmetric multipole expansions in FMM at 10⁵–10⁶ bodies.
- **Energy-Conserving Surrogate Training:** Hamiltonian Neural Networks, Symplectic Networks, and multi-step loss regularization (ℒ = ℒ_force + λ_E |Ḣ| + λ_L ‖ΔL‖) to prevent secular energy leakage during long-horizon rollouts.

</details>

<details>
<summary><strong>🧬 hPSC Gene Regulatory Network Interface</strong> — stochastic pluripotency model</summary>

<br>

Stochastic nonlinear dynamical model of human pluripotent stem-cell fate. The OCT4–SOX2–NANOG–GATA6–PAX6 circuit is reduced to a two-axis **P / D** system (pluripotency vs differentiation) with Hill-type cooperative activation/repression and a **Chemical Langevin Equation** stochastic layer. Built and numerically validated end-to-end in GNU Octave 8.4.0 — no external packages, ~70 s runtime.

Key results: Newton–Raphson fixed-point search recovers **genuine tristability** (3 stable + 2 saddle fixed points at κ = 1.6); κ-bifurcation sweep shows tristability robust for κ ≳ 0.6 across a >4× parameter range with a pitchfork-type stability-exchange near κ ≈ 0.38 bracketed by two saddle-node annihilations — richer than the textbook single-pitchfork picture. **Waddington quasi-potential** reconstructed from a 70-trajectory CLE ensemble; Hessian curvature cross-checked via exact **Lyapunov route** (stable wells) and empirical histogram route — discrepancy attributed to finite-bin + kernel smoothing, documented explicitly.

**Next:** explicit GATA6 third axis · bursting-aware CLE (Kursawe–Galla 2025) · L1-regularised **W** from scRNA-seq + scATAC-seq · transition-path barrier heights → iPSC reprogramming first-passage times.

**Patent readiness (15 Oct 2026 review):** Not established — needs scientific corrections, reproducibility improvements, and prior-art comparison before IDF submission. Original files and enabling details kept in confidential channels pending Cell clearance.

</details>

<details>
<summary><strong>🔥 Hybrid Wildfire Modeling</strong> — differentiable CA + GNN fire prediction</summary>

<br>

5-layer hybrid wildfire prediction system fusing USGS DEM terrain, LANDFIRE fuel models, NOAA NDFD weather, and NASA FIRMS satellite hotspots. A **differentiable cellular automaton** (PyTorchFire, GPU) implements the Rothermel spread model with Huygens elliptical anisotropy; a lightweight **Graph Attention Network** (~30–50k params) runs in parallel on an adaptive quad-tree mesh (250 m → 60 m near fire front, 60–70% memory saving vs uniform grid) to output per-node spot-fire probability, spread-speed correction, and direction bias — recovering **~75–80% spot-fire recall vs ~40% for CA alone**. **Real-time gradient-descent calibration** fits Rothermel R₀ to satellite fire boundaries (IoU + Hausdorff loss) in under 2 min on an A100.

**2020 Diablo Wind Fire benchmark:** hybrid CA+GNN+calibration reaches **0.81 IoU at 6 h in 35 ms/step** vs 0.68 IoU at 850 ms/step for CPU CA. Full specification complete; 16-week implementation roadmap ready.

</details>

<details>
<summary><strong>🧠 GNNs in Neural Cellular Automata</strong> — graph-topology pre-pre-training study</summary>

<br>

**Domain:** Machine Learning · Graph Neural Networks · Language Model Initialization

Independent small-scale study testing whether **graph-NCA synthetic trajectories can improve a transformer's initialization before language pre-training** (pre-pre-training, PPT). The GNN is a frozen random-rule data generator — not a component inside the language model. The study compares graph, grid, and shuffled synthetic trajectories as PPT sources, then feeds all arms into the same downstream language training stage.

Reference: [Training Language Models via Neural Cellular Automata, v1](https://arxiv.org/html/2603.10055v1) · [Author code](https://github.com/danihyunlee/nca-pre-pretraining) (pinned revision `bdd1c71e`, 12 Mar 2026).

**Model:** Small Llama-style transformer — 4.58M-param synthetic model / 12.31M-param language model (different embedding tables for the two vocabularies). 274 shared output symbols: 256 bytes + 16 binary patch symbols + 2 frame markers. Byte perplexity target: 2.5 validation nats/byte.

**Experimental design (v2 / v3):**

```
Arms entering the same N-update language stage:
  scratch       — no PPT, language training from random init
  grid_nca      — K synthetic updates on periodic grid trajectories → language
  graph_nca     — K synthetic updates on rewired graph trajectories → language
  shuffled_grid — frequency-preserving shuffled grid trajectories → language
  shuffled_graph — frequency-preserving shuffled graph trajectories → language

Key controls: identical language data order, optimizer init, LR schedule,
batch/context, and evaluation across all arms. Language heads restored to
initial values at the PPT/language boundary.
```

**v2 GPU result (Tesla T4, Oct 2026)** — grid and shuffled, 3 paired seeds, 1000 PPT + 2000 language updates:

| Initialization | Mean final val NLL | Geometric language-token speedup | Geometric cumulative-time speedup |
|---|---|---|---|
| Scratch / no PPT | 5.266091 | 1.000× | 1.000× |
| Grid NCA | 5.233321 | **1.178×** | 0.886× |
| Shuffled NCA | 5.231528 | **1.178×** | 0.883× |

Grid first reached the scratch reference at 1800 / 1600 / 1700 language updates; shuffled at 1700 / 1600 / 1800. All 15 checkpoints passed independent CPU replay (max loss discrepancy 1.96 × 10⁻⁷). Comparable shuffled gains leave the NCA-dynamics-specific benefit unresolved. Cumulative time ~13% higher for grid — cost recovery not demonstrated. No graph treatment in v2; official test unused.

**v3 GPU result (Tesla T4, Oct 2026)** — five arms, 3 paired seeds, 1000 PPT + 2000 language updates:

| Initialization | Mean final val NLL | Geometric language-token speedup vs scratch | Geometric cumulative-time speedup vs scratch |
|---|---|---|---|
| Scratch / no PPT | 5.266091 | 1.000× | 1.000× |
| Grid NCA | 5.237811 | 1.112× | 0.838× |
| Graph NCA | 5.232262 | **1.178×** | 0.872× |
| Shuffled grid | 5.234889 | 1.112× | 0.835× |
| Shuffled graph | 5.234889 | 1.134× | 0.846× |

Graph reached the paired grid endpoint at 1800 / 2000 / not reached for seeds 17 / 29 / 43 — primary all-seed speedup censored. Small average gain does not establish consistent topology-specific acceleration. Cumulative time ~14.7% higher for graph. All 27 stage checkpoints passed CPU replay (max discrepancy 1.86 × 10⁻⁷). Official test unused.

**v4 GPU result (Tesla T4, Oct 2026)** — seven arms with prefix-matched shuffled controls, 6 fresh paired cohorts:

| Initialization | Mean final val NLL | Language-token speedup vs scratch | Cumulative-time speedup vs scratch |
|---|---|---|---|
| Scratch | 5.273956 | 1.000× | 1.000× |
| Grid | 5.230608 | 1.165× | 0.864× |
| Graph | 5.234337 | 1.154× | 0.858× |
| Original shuffled grid | 5.236298 | 1.144× | 0.852× |
| Original shuffled graph | 5.234172 | 1.166× | 0.864× |
| Prefix-matched shuffled grid | 5.235063 | 1.167× | 0.865× |
| Prefix-matched shuffled graph | 5.235680 | 1.154× | 0.858× |

**Both frozen primary graph comparisons fail** — graph/grid: 5 token ties and 1 loss (ratio 0.990×, p=1); graph/prefix-graph: 4 ties, 1 win, 1 loss (1.000×, p=0.984). Graph uses ~13.4% fewer language tokens at the scratch target but ~16.6% more cumulative time. All 78 stage checkpoints passed CPU replay (max discrepancy 2.78 × 10⁻⁷). A post-hoc causal frequency predictor beats all 12 structured PPT models on held-out patch targets — the original unigram/copy gate is insufficient to establish dynamics-specific learning.

**CPU diagnostic stages (v5–v9, Oct 2026):**
- **Stage 5 — readiness:** All 12 v4 PPT cohorts fail both 0.01-nat readiness margins; language guard rejects them.
- **Stage 6 — trainability:** Full backbone learns binary complement rule — 3/3 coherent seeds pass, 100% held-out accuracy.
- **Stage 7 — spatial bridge:** Neighbor-parity rule; accuracy 91.84%. Supplementary first-transition diagnostic: original/intervention accuracy 47.40% / 42.08%; both correct in only 19.95% of eligible pairs — partial rule learning only.
- **Stage 8 — loss weighting:** Sixfold first-transition weighting worsens all 3 coherent seeds on original and intervened first-patch NLL. Full-trajectory readiness still passes, confirming trajectory gates cannot establish first-transition competence.
- **Stage 9 — fit vs generalization:** No new training; all 15 checkpoints re-scored on train/dev/assessment splits. Seeds 149/167 improve training NLL with weighting but worsen on held-out splits; seed 131 worsens everywhere. Four-patch assessment accuracy rises 42.90% → 46.48% with weighting despite first-patch regression.

Local suite: 122 tests passing. **Formal verification:** LaTeX note + Lean 4.35.0, 44 checked theorem statements; coverage partial — entropy, spectral, and Taylor remainder arguments remain informal.

**Next:** Initial-condition diversity ablation — separately frozen, not yet configured.

</details>

<details>
<summary><strong>📐 Unified Linear Network Theorem</strong></summary>

<br>

Open theoretical question — notes only, no implementation yet.

</details>

---

## 🛰️ What drives all of this

- How do you design computational integrators and training algorithms that leak less energy over extended temporal horizons?
- How can an autonomous assistant enforce strict security boundaries in code rather than trusting prompt instructions?
- Can a small robot navigate using imperfect sensors and still explain its internal state?
- When does a stochastic model of a biological network stop being a diagram and start generating real predictions?
- Can physics-grounded simulation plus a light learned correction beat a pure neural model on speed, accuracy, and out-of-distribution generalization simultaneously?
- How can a control system move from a simulation to a test bench without skipping the hard engineering questions in between?

I also keep an **ideas notebook** — problems in autonomy, manufacturing, metrology, and flight systems. Some ideas are seeds, not promises; the work is figuring out which ones deserve a prototype.

---

## 🛠️ Things I work with

`Python` · `C/C++` · `JavaScript` · `Numerical simulation & Symplectic integrators` · `Applied Mathematics` · `asyncio & Systems architecture` · `Embedded systems (ESP8266/ESP32)` · `Robotics` · `DSP (JUCE / WASAPI)` · `Control systems` · `WebAssembly` · `GNU Octave / MATLAB / Simulink` · `PyTorch · GNNs` · `React + Node · SQLite`

---

### Find me around GitHub

[Repositories](https://github.com/code8286?tab=repositories) · [GravBox source](https://github.com/code8286/gravbox) · 

<p align="center"><sub>Curiosity in, Explosives out. Repeat.</sub></p>
