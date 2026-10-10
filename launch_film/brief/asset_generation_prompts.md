# PRIVREACH 5-MINUTE LAUNCH FILM — ASSET GENERATION PROMPTS & SPECIFICATIONS

This document catalogs the exact generative prompts, algorithmic seeds, and motion parameters used across all 6 film sequences.

---

### SCENE 01: THE FRAGMENTATION (00:00 – 00:30)
- **Asset 1A: Fragmented Scientific Cards on White**
  - **Tool/Engine**: Python PIL / Procedural Vector Layout Engine
  - **Prompt / Specification**:
    > *Architectural minimalist white canvas (#FAFAF8) with faint 1px slate grid (step 80px). Scattered scientific artifacts floating adrift: an isolated LaTeX mathematical formula ($C_L = 2L/(\rho v^2 S)$), a single research paper excerpt card with micro-elevation, a disconnected experimental tabular matrix, and fragmented network nodes. Tendril lines reaching toward center but stopping short with deliberate gaps. Subtle slow camera pull-back (1.05 to 1.00).*
- **Asset 1B: Central Electric-Blue Activation Point**
  - **Prompt / Specification**:
    > *Single saturated Electric Blue dot (#245CFF) illuminating at mathematical center at t=25.0s. Three concentric acoustic alignment rings pulsing outward (radii 24px, 48px, 72px) at 6 Hz. Surrounding cards dampening drift physics and snapping to Cartesian grid.*

---

### SCENE 02: THE REVEAL (00:30 – 01:10)
- **Asset 2A: Geometric Coordinate Convergence**
  - **Prompt / Specification**:
    > *Clean 2D Cartesian coordinate axes extending horizontally and vertically from center blue point with micro-caliper tick marks at 40px intervals. Octagonal rotating geometric construction frames dissolving symmetrically into the official Privreach vector mark.*
- **Asset 2B: Official Emblem & Typographic Wordmark**
  - **Asset Source**: `PrivreachDesktop/Assets/logo.png` (1024×1024 Vector-rendered PNG)
  - **Prompt / Specification**:
    > *Centered high-contrast card elevation. Official Privreach vector mark (140×140), bold Ink Navy display wordmark ('PRIVREACH', 54pt bold), and Electric Blue subhead ('Your Private Research Operating Environment.', 22pt).*
- **Asset 2C: Forward Glide into Workstation**
  - **Prompt / Specification**:
    > *Smooth 2.5D push-in scaling from 0.85 to 1.00 over 8 seconds. Dissolving seamlessly into native WinUI 3 desktop application frame with macOS/Windows control dots and subtle ambient drop shadow.*

---

### SCENE 03: INSIDE THE WORKSPACE (01:10 – 02:10)
- **Asset 3A: Three-Panel Interface Overview**
  - **Asset Source**: Native build screenshot (`media_1791563716633_ae3d6b55.png` / `full_workstation.png`)
  - **Prompt / Specification**:
    > *High-fidelity native WinUI 3 interface showing left scientific domain navigation, center computational canvas, and right adversarial verification panel. Animated Electric Blue focus brackets highlighting active architectural zones.*
- **Asset 3B: 100×100 Computational Dot Matrix Animation**
  - **Tool/Engine**: Procedural 2D Wave Equation Solver (NumPy + PIL)
  - **Prompt / Specification**:
    > *100×100 fluid simulation canvas. 2,500 active coordinate points modulated by dual-radial shockwave interference formula: $f(x,y,t) = \sin(r \cdot 0.45 - \omega t) + \cos(x \cdot 0.3 + 0.8\omega t)$. Wave crests illuminated in Electric Blue; resting nodes in Soft Slate. Right HUD telemetry displaying Mach 0.78, Re 6.5×10⁶, L/D 18.42.*
- **Asset 3C: Hardware Resource Monitors & Model Status**
  - **Truth Status**: 100% Verified against live `/api/status` daemon
  - **Prompt / Specification**:
    > *Hardware telemetry card showing real operating metrics: CPU 7.2%, RAM 0.6 / 32 GB, Gemma 3 1B IT local in-process GGUF engine ('ONLINE' in Mint Green), and Airgap active badge.*

---

### SCENE 04: FROM SOURCE TO INSIGHT (02:10 – 03:30)
- **Asset 4A: Source Document & Dynamic Bracketing**
  - **Asset Source**: Ingested `sample_wing_aerodynamics.pdf` (PyMuPDF verified)
  - **Prompt / Specification**:
    > *High-resolution white PDF document card. Header: 'Aerodynamic Principles of Subsonic Airfoils'. Lift equation $C_L = 2L/(\rho v^2 S)$ framed by animated pulsing Electric Blue selection brackets.*
- **Asset 4B: Vector Link Tracing & Evidence Matrix**
  - **Prompt / Specification**:
    > *Antialiased vector line drawing from page 1 into Claim Card [1]. Grounding confidence 100.0%. Interactive citation pill 📄 [1] sample_wing_aerodynamics.pdf (p. 1) connecting chat output to exact document page.*
- **Asset 4C: Deterministic SymPy Proof & Verification Badge**
  - **Truth Status**: 100% Verified against SymPy AST solver
  - **Prompt / Specification**:
    > *Python AST sandbox derivation card. Exact solution $C_L = 0.2798$. Mint Green audit badge: [✓ VERIFIED (0.0% ERROR)]. Ground truth calculation proven against model claims.*

---

### SCENE 05: THE LARGER VISION (03:30 – 04:30)
- **Asset 5A–5G: Seven Scientific Discipline Schematics**
  - **Prompt / Specification**:
    > *Expansive constellation of 7 technical disciplines on white canvas: (1) NACA 64-416 Airfoil streamlines, (2) Thermodynamics adiabatic PV curve, (3) Double-helix pharmacokinetics, (4) Benzene molecular geometry with OH group, (5) Multi-joint kinematic robotic arm, (6) Differential tensor manifold, (7) Finite element truss under stress. Connected by pulsing Electric Blue interdisciplinary vector lines.*

---

### SCENE 06: THE LAUNCH / END CARD (04:30 – 05:00)
- **Asset 6A: Minimalist End Card & Brand Resolve**
  - **Prompt / Specification**:
    > *Scientific diagrams collapsing into a calm Cartesian grid. Screen settling into pure architectural white. Centered master card: official Privreach emblem, bold Ink Navy wordmark 'PRIVREACH', Electric Blue subhead 'RESEARCH, CONNECTED.', editorial subtitle 'Your Private Research Operating Environment.', and GitHub badge pill 'github.com/pranav520214/Privreach'. Holding in serene stillness from 04:52 to 05:00.*
