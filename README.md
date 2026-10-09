# ⚡ Privreach OS v2.0
> **Zero-Trust Local Scientific Workstation & Multimodal Reasoning Operating System**

Privreach OS is a fully air-gapped, zero-trust scientific research operating system designed to run 100% locally on personal workstation hardware (CPU embeddings + 4GB VRAM). It unifies deep literature retrieval, multi-document synthesis, adversarial claim auditing, deterministic mathematical verification, and cross-document knowledge graphing into a seamless native desktop environment.

---

## 🌟 Key Architecture & Capabilities

### 1. 🖥️ Native Fluent Desktop Workstation (WinUI 3)
- Built with **.NET 8 Windows App SDK** featuring Mica alt backdrop, acrylic navigation, and hardware-accelerated smooth animations.
- **Synchronized Split PDF Workspace**: Direct jump to citation pages with bounding box highlight tracking.
- Non-blocking asynchronous UI with STA-safe dispatcher queue marshaling.

### 2. 🌐 Three-Plane Research Web Workstation
- Accessible at **`http://127.0.0.1:7860`** using Gradio.
- **Left Plane**: Dual-model RLCD inquiry console with real-time risk classification.
- **Center Plane**: Explainer Canvas with interactive LaTeX mathematics, Plotly 2D/3D visualizations, and particle simulations.
- **Right Plane**: Evidence & Media Vault displaying visual textbook diagrams and time-aligned audio/video chunks.

### 3. 📊 Advanced Document Understanding (Vision RAG)
- Multi-modal PDF ingestion extracting high-resolution formulas, tables, and chemical diagrams.
- Clean LaTeX normalization and symbol sanitation.

### 4. 🧠 Deep Thinking & Reasoning (R1 / CoT Integration)
- Native support for reasoning models (DeepSeek-R1, Qwen-2.5-Coder).
- Real-time `<think>` trace decomposition with collapsible step-by-step audit trail.

### 5. 🕸️ GraphRAG & Cross-Document Citation Network
- In-RAM semantic knowledge graph powered by NetworkX.
- Automated Louvain community clustering and cross-document citation bridge detection.
- Fast sub-graph exploration and interactive ASCII/Markdown topological maps.

### 6. 🔄 Modern Patching & Updation System
- **Atomic Differential Patches (`.privpatch`)**: Cryptographically verified (SHA-256) delta packages.
- **Pre & Post Condition Validation**: Prevents corrupted patching before touching disk.
- **Instant Point-in-Time Snapshots**: Automatic file snapshots before every patch operation.
- **Zero-Downtime Rollbacks**: One-click restoration to previous good state.
- **Live In-RAM Hot-Patching**: Dynamically reloads Python modules without server restarts.
- **Unified REST API & CLI**: Full update management via `/api/updater/*` and `.\update.ps1`.

---

## 🚀 Quickstart Guide

### Prerequisites
- Windows 10/11 x64
- .NET 8.0 SDK
- Python 3.11+
- Local Ollama instance (e.g. `qwen2.5:0.5b` and `qwen2.5-coder:3b`)

### 1. Launching the Native Desktop Workstation
```powershell
cd E:\PrivreachOS
.\run_desktop.ps1
```
*(Or run `python run_desktop.py`)*

### 2. Launching the Browser Web Workstation
```powershell
cd E:\PrivreachOS
.\run_web.ps1
```
Open **[http://127.0.0.1:7860](http://127.0.0.1:7860)** in your browser.

### 3. Patching, Updates & Rollbacks
```powershell
# Check current version status and snapshot history
.\update.ps1 -Status

# Check for remote/local OTA updates
.\update.ps1 -Check

# Apply a .privpatch bundle with automated snapshot & validation
.\update.ps1 -Apply path\to\update.privpatch

# Revert to the latest snapshot if needed
.\update.ps1 -Rollback

# List all rollback points
.\update.ps1 -Snapshots
```

### 4. Running the Verification Suite
```powershell
.\venv\Scripts\pytest.exe -v
```
All 55+ tests run in under 2 minutes.

---

## 🔒 Zero-Trust Privacy Guarantee
- 100% of embeddings and vector searches execute locally in RAM using CPU MiniLM.
- 0% cloud API dependencies, zero external data telemetry, zero telemetry egress.
