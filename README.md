<div align="center">
  <img src="assets/logo.png" alt="Privreach Logo" width="280">
  
  # ⚡ Privreach
  **Zero-Trust, 100% Local Scientific & Engineering Operating System**  
  *Dual-Model Adversarial Verification • CPU Embeddings + 4GB VRAM • Zero Data Egress*

  <p>
    <code>🔒 PRIVACY</code> &nbsp;•&nbsp;
    <code>💻 LOCAL AI</code> &nbsp;•&nbsp;
    <code>📖 SCIENTIFIC KNOWLEDGE</code> &nbsp;•&nbsp;
    <code>🛡️ VERIFICATION</code>
  </p>
</div>

---


## ⚡ Why Privearch?

Standard AI chatbots guess the next word. In science, medicine, and engineering, guessing leads to dangerous hallucinations. Privearch treats information retrieval and synthesis like an Operating System:

- 🧠 **Dual-Model "Brain-Trust"**: Employs a tiny, lightning-fast **0.5B parameter model** (`qwen2.5:0.5b`) strictly for administrative query routing, risk classification, and safety verification, while reserving a heavier **3B/4B model** (`qwen2.5-coder:3b`, `qwen3.5:4b`, `medgemma:4b`) for deep scientific synthesis.
- 🛡️ **Adversarial Verification**: For high-risk scientific inquiries, the system audits its own answer. It breaks generated responses down into atomic factual claims, cross-references each against the source PDFs, and highlights unsupported or contradictory claims before presenting them to the user.
- 📚 **Dynamic Ingestion**: Drag and drop any PDF into the terminal or web console. The system instantly extracts the text, constructs semantic sliding-window chunks, vectorizes them via CPU embeddings (`all-MiniLM-L6-v2`), and updates in-RAM **Okapi BM25** and **FAISS** indexes dynamically.
- 🔒 **Zero-Trust & 100% Local**: No API keys. No cloud compute. Not a single prompt or PDF leaves your machine. Specifically tuned to run on consumer hardware (CPU + 4GB VRAM).

---

## 🏗️ The RLCD Architecture


```
[ User Query ] ──► [ R: Router (0.5B) ] ──► Schema: {Risk: CRITICAL, Task: SYNTHESIS, Entities: [...]}
                          │
                          ▼
                   [ L: Logic (Hybrid Retriever) ]
                          │
            ┌─────────────┴─────────────┐
            ▼                           ▼
     [ Okapi BM25 ]              [ FAISS Vector ]
     (Lexical in RAM)            (Semantic in RAM)
            └─────────────┬─────────────┘
                          ▼
            [ Reciprocal Rank Fusion (RRF) ]
                          │
                          ▼ Top-K Grounded Passages
                   [ C: Control (4B Synthesis Engine) ]
                          │
                          ▼ Academic Answer with Citations [1], [2]
                   [ D: Decision (0.5B Adversarial Verifier) ]
                          │
            ┌─────────────┴─────────────┐
            ▼                           ▼
    [ Claim Deconstruction ]   [ Source Cross-Audit ]
            └─────────────┬─────────────┘
                          ▼
              [ Claim Verification Matrix ]
       (VERIFIED ✓ | UNSUPPORTED ⚠️ | CONTRADICTION ❌)
                          │
                          ▼
           [ Peer-Reviewed Grounded Output ]
```


### 1. Query Analyzer (0.5B) [Router]
Intercepts the query and tags it with a validated Pydantic schema:
- `RiskLevel`: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`
- `TaskType`: `LITERATURE_REVIEW`, `MECHANISTIC_SYNTHESIS`, `FACT_CHECK`, `SAFETY_AUDIT`, `CALCULATION_DERIVATION`
- `KeyEntities`: Chemical names, equations, constants
- `LexicalKeywords` & `SemanticQueries`: High-signal query variants for retrieval


### 2. Hybrid Retriever (RRF) [Logic]
Fuses lexical precision with semantic understanding in RAM:
- **Okapi BM25**: Robertson-Spärck Jones IDF with length normalization ($k_1=1.5, b=0.75$)
- **FAISS / Dense Vector Index**: $L_2$-normalized cosine similarity over 384-d CPU embeddings
- **Reciprocal Rank Fusion**:
  $$RRF(d) = \sum_{m \in \{BM25, FAISS\}} \frac{1}{60 + \text{rank}_m(d)}$$

### 3. Synthesis Engine (4B) [Control]
Reads retrieved chunks tagged with explicit page and document markers. Produces structured, peer-review grade text with strict bracket citations `[1]`, `[2]`. Explicitly declines to guess if data is missing.

### 4. Adversarial Verifier (0.5B) [Decision]
Audits the synthesis answer claim-by-claim before displaying it:
- Deconstructs text into atomic factual propositions
- Checks claims against the cited source chunks
- Assigns verification status: `VERIFIED ✓`, `UNSUPPORTED ⚠️`, `CONTRADICTED ❌`, `PARTIAL ⚡`
- Computes **Grounding Confidence Score** ($0 - 100\%$)
- Injects highlighted warnings directly above unverified claims

---

## 💻 Windows Native Executables & One-Click Installer

Privearch is available as native Windows `.exe` executables with custom application icons and installer:

| File | Type | Description |
|---|---|---|
| [`Privearch-Setup.exe`](file:///c:/Users/RYZEN/Downloads/chemistry/Privearch-Setup.exe) | **One-Click Installer** | Installs Privearch to `%LOCALAPPDATA%\Programs\Privearch`, creates Desktop & Start Menu shortcuts, and registers `privearch` in Windows PATH. |
| [`Privearch.exe`](file:///c:/Users/RYZEN/Downloads/chemistry/Privearch.exe) | **Desktop Executable** | Double-click to launch the Web Dashboard; auto-starts Ollama and auto-opens default browser to `http://127.0.0.1:7860`. |
| [`Privearch-Terminal.exe`](file:///c:/Users/RYZEN/Downloads/chemistry/Privearch-Terminal.exe) | **Terminal OS Executable** | Double-click to launch directly into the futuristic interactive Rich Terminal Operating System. |

### Command Line Options (`Privearch.exe`)
```cmd
Privearch.exe            :: Launch Modern Web Dashboard (Default)
Privearch.exe --cli      :: Launch Interactive Rich Terminal OS
Privearch.exe --engine   :: Auto-Install & Configure Local Ollama Engine & Models
Privearch.exe --update   :: Over-The-Air (OTA) System Updater
Privearch.exe --vault    :: Re-index all scientific PDFs into Vault
Privearch.exe --help     :: Show launcher help
```

---

## ⚡ Zero-Friction Self-Installing AI Engine

Privearch eliminates all manual AI setup:
- **100% Free & Local**: No paid API keys, no subscriptions, no external cloud dependencies.
- **Automatic Engine Provisioning**: If Ollama is not installed on the system, Privearch automatically downloads the official Windows installer and executes it silently.
- **Automated Model Pulling**: Automatically fetches the required models (`qwen2.5:0.5b` and `qwen2.5-coder:3b`) with real-time download and verification bars.
- **1-Click Web Management**: Manage, status-check, or pull additional models (e.g. `llama3.2:1b`, `medgemma:4b`, `qwen3.5:4b`) directly from the **"⚡ AI Engine & Self-Setup"** tab in the Web Dashboard.
- **Terminal Management**: Run `/engine` inside the Terminal OS or execute `Privearch.exe --engine`.


---

## 🔄 Global Over-The-Air (OTA) Updates

Privearch features a zero-trust, cryptographically verified OTA update engine (`OTAManager`):
- **Cryptographic SHA-256 Signatures**: Every incoming update package is strictly verified against its SHA-256 hash before extraction.
- **Vault Cache Protection**: Updates **strictly preserve** the `.privearch_cache/` knowledge vault and personal data—your pre-indexed chemistry textbooks are never overwritten.
- **Atomic Safety & Automatic Rollback**: If an update or verification fails, Privearch automatically rolls back to the previous stable snapshot.

### Updating via Web Dashboard
1. Open the **🔄 OTA System Updates** tab in the Privearch Web UI.
2. Click **🔍 Check for Updates** to view the latest version and release notes.
3. Click **⚡ Download & Apply Update** for seamless 1-click update.

### Updating via Terminal
```cmd
privearch --update
:: Or inside the interactive terminal prompt:
privearch@os ~ $ /update
```

---

## 📦 Global Distribution Package (`dist/`)

For deploying Privearch to any Windows machine or distributing globally:
- **`dist/Privearch-v1.0.0-Windows-x64.zip`** (3.87 MB): Complete standalone release with one-click installer, native `.exe` launchers, and pre-indexed 29 chemistry textbooks.
- **`dist/Privearch-Setup.exe`** (414 KB): Native one-click installer wizard.
- **`dist/privearch-ota-v1.0.0.zip`** (0.08 MB): Lightweight OTA update archive for cloud/GitHub releases.
- **`dist/version.json`**: OTA release metadata manifest.

---

## 🚀 Quickstart

### 1. One-Click Desktop Launch
Simply double-click the **Privearch** shortcut on your Windows Desktop or search for **Privearch** in your Start Menu!

### 2. Run via Terminal
```bash
python run_web.py          # Start Web Dashboard
python run_privearch.py    # Start Interactive Terminal OS
```

---

## ⚙️ Configuration (`privearch/config.py`)

| Parameter | Default | Description |
|---|---|---|
| `router_model` | `qwen2.5:0.5b` | 0.5B model for administrative routing & risk tagging |
| `synthesis_model` | `qwen2.5-coder:3b` | 3B/4B model for academic synthesis |
| `verifier_model` | `qwen2.5:0.5b` | 0.5B model for claim-by-claim adversarial verification |
| `embedding_backend` | `cpu_minilm` | CPU embedding engine leaving 100% of 4GB VRAM for LLMs |
| `chunk_size_words` | `150` | Semantic chunk size with 30-word sliding window overlap |
| `rrf_k` | `60` | Reciprocal Rank Fusion constant |
| `zero_trust_airgap` | `True` | Rejects any non-localhost network connections |

## 📚 Documentation
* [System Architecture](docs/architecture.md): In-depth RLCD mathematical and layer formulation.
* [Execution & Data Flows](docs/flows.md): Document ingestion and adversarial audit sequence diagrams.
* [Setup & Operations](docs/setup.md): Complete installation, testing, and air-gapped configuration.

## 📄 License
This project is licensed under the [MIT License](LICENSE).
