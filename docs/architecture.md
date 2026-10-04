# Privearch System Architecture

## 1. Zero-Trust Scientific Synthesis Philosophy

Standard LLM interfaces generate probabilistic token completions without empirical verification against ground-truth scientific literature. Privearch treats scientific query processing as an operating system pipeline:
* **Zero Cloud Compute:** Prompts, clinical records, and proprietary PDFs never leave local hardware.
* **RLCD Routing Framework:** Router $\rightarrow$ Logic $\rightarrow$ Control $\rightarrow$ Decision.
* **Dual-Model Brain-Trust:** Separation of administrative validation (0.5B model) from deep reasoning (4B/7B model).
* **Adversarial Audit Loop:** Every generated claim must cite verified retrieved paragraphs; unmatched assertions are automatically flagged.

---

## 2. Component Architecture

```text
👤 User (Interactive CLI / Streamlit UI)
  │
  ▼
[Query Ingestion & Task Classification (0.5B)]
  │
  ├─────────────────────────────────────────┐
  ▼                                         ▼
[Lexical Index (Okapi BM25)]       [Vector Index (FAISS CPU)]
  │                                         │
  └───────────────────┬─────────────────────┘
                      │ (Reciprocal Rank Fusion - RRF)
                      ▼
        [Synthesis Engine (4B/7B Model)]
                      │
                      ▼
      [Adversarial Claim Verifier (0.5B)]
                      │
                      ▼
     [Audited Academic Synthesis Output]
```

### RLCD Layer Roles:
1. **Router:** Categorizes queries into `TaskType` (`LITERATURE_REVIEW`, `BIO_SIMULATION`, `FORMULATION`) and calculates `RiskLevel` (`LOW`, `ELEVATED`, `CRITICAL`).
2. **Logic (Retrieval):** Dynamically partitions ingested PDFs into recursive semantic chunks, generating CPU embeddings and indexing lexical tokens into BM25 and FAISS in RAM.
3. **Control (Synthesis):** Formulates contextualized prompts with strictly constrained citation boundaries.
4. **Decision (Verification):** Extracts factual propositions from generated text and performs reverse-lookup against retrieved context spans.
