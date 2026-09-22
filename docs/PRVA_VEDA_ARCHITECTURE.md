# PRVA VEDA ARCHITECTURE

## 1. System Philosophy
Prva Veda is a completely local scientific research system governed by **RLCD (Routing, Logic, Control, and Verification)**. The system prioritizes scientific correctness, evidence traceability, and reproducible execution over unverified language model fluency.

## 2. Core Control Flow
1. **User Query**: Processed by the RLCD Query Classifier to extract Domain, Risk, Complexity, and Task type.
2. **RLCD Router**: Generates a typed execution schema defining the exact path (e.g., standard vs. critical-research mode, required tools, required retrieval).
3. **Retrieval**: Uses a local hybrid pipeline (BM25 + Dense Vectors + Knowledge Graph) to fetch evidence from the scientific corpus.
4. **Foundational SLM & Specialists**: The selected small language model (3B-8B parameter scale) interprets the evidence and generates a candidate response with discrete claims.
5. **RLCD Verifier**: Dissects the response into testable claims and runs adversarial validation (citation checking, mathematical verification, contradiction detection).
6. **Repair Loop / Final Synthesis**: If claims are unsupported, the pipeline loops. Otherwise, it compiles a final response with provenance.

## 3. Storage and Repository Layout
The project is maintained at `E:\Prva_Veda` with the following distinct functional layers:
- `core/`: Schemas (Pydantic), orchestration, and general configuration.
- `rlcd/`: The brain of the system, containing discrete components for routing, classification, policy, verification, and confidence aggregation.
- `models/`: Storage for the Foundation SLM, LoRA specialists, and verifier models.
- `knowledge/`: Local databases, vector indexes, BM25, and the scientific Knowledge Graph.
- `datasets/`: Extracted datasets from the corpus pipeline (Pretraining, Instruction, Routing).
- `tools/`: Deterministic execution environments (Python, SymPy, simulators).
- `memory/`: Long-term episodic and verified semantic storage.

## 4. Hardware Alignment (Constraint-Aware)
Given the constraints of a 16GB RAM + 4GB VRAM environment:
- **Inference Engine**: Native Hugging Face `transformers` will be bypassed for reasoning in favor of `llama.cpp` using local GGUF models.
- **Model Scale**: Foundational SLMs must be aggressively quantized (e.g., 4-bit or 5-bit GGUF). Models such as `Cerberus-4B`, `Huihui-Qwen3.5-4B`, or `Llama-3.1-8B` are viable candidates.
- **Specialists**: Implemented as dynamically loaded LoRA adapters over the base model, ensuring VRAM is not exhausted by keeping multiple standalone models in memory.

## 5. Phased Implementation Roadmap
- [x] **PHASE 1**: Corpus (Implemented externally at `E:\Prva_Veda_Research_Library\dataset_builder`)
- [ ] **PHASE 2**: Retrieval
- [ ] **PHASE 3**: Foundation model adaptation
- [ ] **PHASE 4**: Scientific instruction tuning
- [ ] **PHASE 5**: RLCD router
- [ ] **PHASE 6**: Tools integration
- [ ] **PHASE 7**: Verification
- [ ] **PHASE 8**: Specialist models
- [ ] **PHASE 9**: Learning RLCD
- [ ] **PHASE 10**: Evaluation
