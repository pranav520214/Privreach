import sys
from pathlib import Path
from huggingface_hub import hf_hub_download

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from core.orchestration.pipeline import PrvaVedaPipeline

def test_router():
    corpus_path = r"E:\Prva_Veda_Research_Library\datasets\retrieval\chunks.jsonl"
    
    print("Locating baseline SLM for routing...")
    repo_id = "mradermacher/Huihui-Qwen3.5-4B-abliterated-GGUF"
    filename = "Huihui-Qwen3.5-4B-abliterated.Q4_K_M.gguf"
    
    try:
        model_path = hf_hub_download(repo_id=repo_id, filename=filename)
    except Exception as e:
        print(f"Failed to locate model: {e}")
        return

    pipeline = PrvaVedaPipeline(model_path=model_path, corpus_path=corpus_path)
    
    queries = [
        "Hello, how are you today?",
        "I need a literature review on the use of continuous infusion vs intermittent dosing of vancomycin in critically ill patients. Ensure all claims are verified.",
        "Calculate the clearance if the volume of distribution is 0.7 L/kg and the elimination rate constant is 0.05 h^-1 for a 70kg patient."
    ]
    
    for q in queries:
        pipeline.execute(q)

if __name__ == "__main__":
    test_router()
