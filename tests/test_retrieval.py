import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from knowledge.retrieval.hybrid_search import HybridRetriever

def test_hybrid_search():
    corpus_path = r"E:\Prva_Veda_Research_Library\datasets\retrieval\chunks.jsonl"
    
    if not Path(corpus_path).exists():
        print(f"Skipping test, corpus not found at {corpus_path}")
        return
        
    retriever = HybridRetriever(corpus_path)
    retriever.initialize()
    
    queries = [
        "Population pharmacokinetics of Vancomycin",
        "What is the effect of renal function on clearance?",
        "Model-Informed Precision Dosing (MIPD) tools"
    ]
    
    for q in queries:
        print(f"\n{'='*50}")
        print(f"Query: {q}")
        print(f"{'='*50}")
        
        evidence = retriever.search(q, top_k=3)
        
        for i, chunk in enumerate(evidence.chunks):
            print(f"[{i+1}] Score: {chunk.score:.4f} | Source: {chunk.title or 'Unknown'}")
            print(f"    Text: {chunk.text[:150]}...")
            print("-" * 50)
            
if __name__ == "__main__":
    test_hybrid_search()
