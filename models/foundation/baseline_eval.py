import sys
from pathlib import Path
from huggingface_hub import hf_hub_download

sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from knowledge.retrieval.hybrid_search import HybridRetriever
from llama_cpp import Llama

def evaluate_baseline():
    print("1. Initializing Retrieval System...")
    corpus_path = r"E:\Prva_Veda_Research_Library\datasets\retrieval\chunks.jsonl"
    retriever = HybridRetriever(corpus_path)
    retriever.initialize()
    
    print("\n2. Downloading/Locating Baseline Foundation Model...")
    # Using Cerberus-4B or Huihui-Qwen3.5-4B as a lightweight SLM baseline
    repo_id = "HattoriHanzo1/Cerberus-4B-GGUF" 
    filename = "Cerberus-4B.Q4_K_M.gguf"
    
    try:
        model_path = hf_hub_download(repo_id=repo_id, filename=filename)
        print(f"Model located at: {model_path}")
    except Exception as e:
        print("Could not find/download Cerberus-4B, falling back to Qwen...")
        repo_id = "mradermacher/Huihui-Qwen3.5-4B-abliterated-GGUF"
        filename = "Huihui-Qwen3.5-4B-abliterated.Q4_K_M.gguf"
        model_path = hf_hub_download(repo_id=repo_id, filename=filename)
        print(f"Model located at: {model_path}")

    print("\n3. Loading Model via llama.cpp...")
    # Load model with some GPU offloading if CuBLAS is available, otherwise CPU
    llm = Llama(
        model_path=model_path,
        n_ctx=8192, # increased context window to accommodate evidence
        n_gpu_layers=10, # offload 10 layers to 4GB VRAM
        verbose=False
    )
    
    print("\n4. Running RAG Evaluation...")
    queries = [
        "What are the initial dosage recommendations for Vancomycin in Chinese ICU Neonates?",
        "How do Model-Informed Precision Dosing (MIPD) tools improve clinical outcomes?"
    ]
    
    for query in queries:
        print(f"\n{'='*60}")
        print(f"QUERY: {query}")
        print(f"{'='*60}")
        
        # Step 4a: Retrieve Evidence
        print("-> Retrieving evidence...")
        evidence_pkg = retriever.search(query, top_k=3)
        context = evidence_pkg.to_prompt_context()
        
        # Step 4b: Construct Prompt
        # Using a standard ChatML or generic prompt format
        prompt = f"""<|im_start|>system
You are Prva Veda, a highly rigorous scientific research AI. Use the provided Evidence chunks to answer the user's question accurately. If the evidence is insufficient, state that you do not know. 
Evidence:
{context}
<|im_end|>
<|im_start|>user
{query}
<|im_end|>
<|im_start|>assistant
"""
        
        # Step 4c: Generate Response
        print("-> Generating response (this may take a moment on CPU/Partial GPU)...")
        output = llm(
            prompt,
            max_tokens=256,
            temperature=0.1,
            stop=["<|im_end|>"],
            echo=False
        )
        
        response_text = output['choices'][0]['text'].strip()
        print("\nRESPONSE:")
        print(response_text)
        print("-" * 60)

if __name__ == "__main__":
    evaluate_baseline()
