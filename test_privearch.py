"""Automated end-to-end test suite for Privearch OS."""

import os
import sys

# Ensure UTF-8 on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from privearch.config import PrivearchConfig
from privearch.os_engine import PrivearchKernel
from privearch.schemas import RiskLevel, TaskType


def test_privearch_pipeline():
    print("=" * 60)
    print("⚡ TESTING PRIVEARCH LOCAL OPERATING SYSTEM PIPELINE")
    print("=" * 60)

    # 1. Initialize Kernel
    print("\n[Step 1] Initializing PrivearchKernel...")
    config = PrivearchConfig()
    kernel = PrivearchKernel(config)
    status = kernel.get_system_status()
    print("System Status:", status)
    assert status["airgap_mode"] is True, "Airgap mode must be True"

    # 2. Ingest PDF
    sample_pdf = "lech101.pdf"
    if not os.path.exists(sample_pdf):
        print(f"File {sample_pdf} not found, skipping ingestion test.")
        return

    print(f"\n[Step 2] Ingesting '{sample_pdf}' dynamically into RAM...")
    ingest_res = kernel.ingest_pdf(sample_pdf)
    print(f"Ingested {ingest_res['doc_name']}: {ingest_res['pages']} pages, {ingest_res['chunks']} chunks in {ingest_res['time_s']}s.")
    assert ingest_res["chunks"] > 0, "Should have created chunks"
    assert kernel.total_chunks > 0, "Total chunks should be > 0"

    # 3. Test RLCD Pipeline
    query = "State Henry's law, write its mathematical formula, and explain its significance in gas solubility."
    print(f"\n[Step 3] Executing RLCD Pipeline for Query: '{query}'")
    report = kernel.execute_rlcd(query)

    print("\n--- 🧠 STAGE 1: ROUTER ANALYSIS ---")
    print(f"Risk Level: {report.query_analysis.risk_level.value}")
    print(f"Task Type: {report.query_analysis.task_type.value}")
    print(f"Domain: {report.query_analysis.scientific_domain}")
    print(f"Key Entities: {report.query_analysis.key_entities}")
    print(f"BM25 Keywords: {report.query_analysis.lexical_keywords}")

    print("\n--- 🔍 STAGE 2: HYBRID RETRIEVAL (RRF TOP CHUNKS) ---")
    for sc in report.retrieved_chunks:
        print(f"[{sc.final_rank}] Page {sc.chunk.page_num} | RRF: {sc.rrf_score:.5f} | BM25: #{sc.bm25_rank} | Dense: #{sc.dense_rank}")
        print(f"     Excerpt: {sc.chunk.text[:100]}...")

    print("\n--- 🔬 STAGE 3: SYNTHESIS ENGINE (RAW ANSWER) ---")
    print(report.raw_synthesis[:400] + ("..." if len(report.raw_synthesis) > 400 else ""))

    print("\n--- 🛡️ STAGE 4: ADVERSARIAL VERIFIER (AUDIT MATRIX) ---")
    audit = report.verification
    print(f"Audit Verdict: {audit.overall_verdict}")
    print(f"Grounding Score: {audit.grounding_score}%")
    print(f"Total Claims Audited: {audit.total_claims}")
    print(f"Verified: {audit.verified_count} | Unsupported: {audit.unsupported_count} | Contradicted: {audit.contradicted_count}")
    
    for c in audit.claims[:5]:
        print(f"  Claim #{c.claim_id}: [{c.status.value}] {c.text[:70]}...")
        if c.evidence_quote:
            print(f"    Evidence Quote: {c.evidence_quote[:70]}...")

    print("\n--- 📊 SYSTEM EXECUTION STATS ---")
    print("Timings:", report.execution_stats["stage_timings"])
    print("Total Elapsed:", report.execution_stats["total_elapsed_ms"], "ms")
    print("Models Used:", report.execution_stats["models_used"])

    print("\n" + "=" * 60)
    print("✅ PRIVEARCH TEST PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    test_privearch_pipeline()
