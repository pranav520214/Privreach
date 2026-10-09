"""Tests for Privearch retrieval engine (BM25 and Hybrid RRF)."""

import pytest
from privearch.schemas import DocumentChunk
from privearch.retrieval.bm25 import InRamBM25, tokenize_scientific
from privearch.retrieval.hybrid_rrf import HybridRRFRetriever


def test_scientific_tokenizer():
    text = "The boiling point of H2O is 373.15K at 101.3 kPa (standard atm)."
    tokens = tokenize_scientific(text)
    assert "h2o" in tokens
    assert "373.15k" in tokens
    assert "101.3" in tokens
    assert "kpa" in tokens


def test_bm25_retrieval():
    chunks = [
        DocumentChunk(
            chunk_id="chunk-1",
            doc_id="doc-chem",
            doc_name="Thermodynamics of Water",
            page_number=12,
            text="Water (H2O) has a high specific heat capacity of 4.184 J/g K."
        ),
        DocumentChunk(
            chunk_id="chunk-2",
            doc_id="doc-chem",
            doc_name="Ethanol Properties",
            page_number=15,
            text="Ethanol (C2H5OH) boils at 351.52 K and is miscible with water."
        ),
        DocumentChunk(
            chunk_id="chunk-3",
            doc_id="doc-physics",
            doc_name="Quantum Mechanics",
            page_number=45,
            text="Schrodinger equation describes the wave function of physical systems."
        ),
    ]

    bm25 = InRamBM25()
    bm25.add_chunks(chunks)

    results = bm25.search("specific heat capacity H2O", top_k=2)
    assert len(results) > 0
    top_idx, top_score = results[0]
    assert bm25.chunks[top_idx].chunk_id == "chunk-1"
    assert top_score > 0
