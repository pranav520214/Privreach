<div align="center">
  
# 🧬 Privearch
**Offline, Zero-Trust STEM Research Assistant for Consumer Hardware**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Local Execution](https://img.shields.io/badge/Execution-100%25%20Local-brightgreen)](#)

*Privearch* (formerly Prva Veda) is a rigorously designed, locally hosted AI pipeline intended for critical scientific research. It reads your clinical, mathematical, and STEM PDFs and synthesizes answers using a dual-LLM architecture that actively audits itself against hallucinations.

</div>

---

## ⚡ Why Privearch?

Standard AI chatbots guess the next word. In science, medicine, and engineering, guessing leads to dangerous hallucinations. **Privearch acts like an Operating System, not a chatbot.**

- **🧠 Dual-Model "Brain-Trust":** Uses a tiny, lightning-fast 0.5B model strictly for administrative routing and safety verification, while reserving a heavier 4B/8B model for deep scientific synthesis.
- **🛡️ Adversarial Verification:** For high-risk questions, the system literally audits its own answer. It breaks its generated response into factual claims and verifies them against the original PDFs, highlighting unsupported claims.
- **📚 Dynamic Ingestion:** Drag and drop any PDF into the terminal. The system instantly extracts the text, builds semantic chunks, vectorizes them via CPU embeddings, and dynamically updates its FAISS and BM25 indexes in RAM.
- **🔒 Zero-Trust & 100% Local:** No API keys. No cloud compute. Not a single prompt or PDF leaves your machine. Designed to run on consumer hardware (CPU + 4GB VRAM).

## 🏗️ Architecture

Privearch uses an **RLCD (Router, Logic, Control, Decision)** architecture:
1. **Query Analyzer (0.5B):** Intercepts the user query and tags it with a Pydantic schema (e.g., `RiskLevel: CRITICAL`, `TaskType: LITERATURE_REVIEW`).
2. **Hybrid Retriever (RRF):** Fuses Okapi BM25 (lexical) and FAISS (semantic) to retrieve the exact scientific paragraphs needed.
3. **Synthesis Engine (4B):** Reads the retrieved chunks and generates a structured, academic answer.
4. **Adversarial Verifier (0.5B):** Double-checks the 4B model's math and factual claims before showing you the screen.

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Visual Studio C++ Build Tools (Windows only, for `llama-cpp-python`)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/privearch.git
   cd privearch
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   # For Windows users installing llama-cpp-python:
   pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
   ```

4. **Run the Interactive Terminal Interface:**
   ```bash
   python chat_interface.py
   ```

## 🖥️ Usage

When you launch `chat_interface.py`, you will be greeted by the Main Menu:

```text
--- Main Menu ---
1. Ingest PDF (Type '1')
2. Enter Chat Mode (Type '2')
3. Exit (Type '3')
```
* **To add knowledge:** Press `1` and drag-and-drop a scientific PDF into the terminal. Privearch will memorize it instantly.
* **To research:** Press `2` and ask complex questions. Watch the RLCD thought process stream in real-time.

## 🤝 Contributing
Contributions are welcome! Whether it's adding new deterministic tools (like Python Code Interpreters for math) or optimizing the prompt pipelines, feel free to open a Pull Request.

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.
