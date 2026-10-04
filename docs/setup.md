# Privearch Setup, Structure, Testing & Operations

## 1. Directory Structure

```text
privearch/
├── configs/               # System and model configuration files
├── core/                  # Core RLCD orchestration and memory interfaces
├── datasets/              # Local scientific PDF repository and parsed text
├── docs/                  # Architectural documentation and runbooks
├── evaluation/            # Automated benchmark evaluation suites
├── experiments/           # Offline evaluation logs and ablation studies
├── knowledge/             # Precomputed BM25 and FAISS indices
├── logs/                  # System operational traces
├── memory/                # Multi-turn conversation and session ledgers
├── models/                # Local GGUF quantized model checkpoints
├── rlcd/                  # Router, Logic, Control, Decision engine
├── scripts/               # Data ingestion, indexing, and export scripts
├── tests/                 # Pytest test suite
├── tools/                 # Deterministic calculation and conversion tools
├── training/              # Fine-tuning and adaptation recipes
├── .env.example           # Safe environment configuration template
├── .gitignore             # Exclusion rules
├── app.py                 # Streamlit graphical interface
├── chat_interface.py      # Interactive terminal console
├── LICENSE                # MIT License
├── README.md              # Public landing page
├── requirements.txt       # Python dependencies
└── run_difficult_questions.py # Hard-question evaluation benchmark
```

---

## 2. Setup Guide

### System Requirements
* Python 3.10+
* 8GB RAM minimum (16GB recommended for full 7B local synthesis)
* C++ Build Tools (Windows) for `llama-cpp-python` compilation

```bash
# Clone repository
git clone https://github.com/pranav520214/privearch.git
cd privearch

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Windows CPU-accelerated llama-cpp installation:
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu

# Copy environment template
cp .env.example .env
```

---

## 3. Running Privearch

```bash
# Launch interactive terminal assistant
python chat_interface.py

# Launch Streamlit web dashboard
streamlit run app.py

# Run difficult STEM benchmark test
python run_difficult_questions.py
```

---

## 4. Testing & Verification

```bash
# Execute automated test suite
pytest tests/ -v
```

---

## 5. Security & Isolation

* **100% Air-Gapped Capable:** Privearch runs entirely without internet access once models are downloaded.
* **No Telemetry:** No user queries, ingested PDFs, or generated summaries are transmitted to external servers.
