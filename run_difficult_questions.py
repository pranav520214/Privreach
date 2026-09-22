import sys
from pathlib import Path
from huggingface_hub import hf_hub_download

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
sys.path.append(str(Path(__file__).parent))

from core.orchestration.pipeline import PrvaVedaPipeline

def main():
    print("Loading Prva Veda for Difficult Queries Test...")
    corpus_path = r"E:\Prva_Veda_Research_Library\datasets\retrieval\chunks.jsonl"
    repo_id = "mradermacher/Huihui-Qwen3.5-4B-abliterated-GGUF"
    filename = "Huihui-Qwen3.5-4B-abliterated.Q4_K_M.gguf"
    
    try:
        model_path = hf_hub_download(repo_id=repo_id, filename=filename)
    except Exception as e:
        print(f"Failed to locate model: {e}")
        return

    pipeline = PrvaVedaPipeline(model_path=model_path, corpus_path=corpus_path)
    
    questions = [
        # 1. Complex Synthesis & Mechanism
        "Compare the impact of extracorporeal membrane oxygenation (ECMO) versus continuous renal replacement therapy (CRRT) on the volume of distribution and clearance of vancomycin in critically ill pediatric patients.",
        
        # 2. Contradiction / Verification Trap
        "Why is it universally recommended to strictly use a one-compartment pharmacokinetic model for vancomycin dosing in neonates, regardless of renal function?",
        
        # 3. Mathematical / Parameter Extraction
        "What are the precise equations used by Model-Informed Precision Dosing (MIPD) tools to estimate the glomerular filtration rate (GFR) in neonates for vancomycin clearance adjustments?"
    ]
    
    for i, q in enumerate(questions):
        print("\n" + "="*80)
        print(f"DIFFICULT QUESTION {i+1}: {q}")
        print("="*80)
        
        try:
            candidate, report, plan = pipeline.execute(q)
            print("\n>>> FINAL SYNTHESIZED RESPONSE <<<")
            print(candidate)
            
            if report:
                print("\n>>> ADVERSARIAL VERIFICATION REPORT <<<")
                print(f"IS SAFE: {report.is_safe}")
                for claim in report.claims:
                    print(f"- CLAIM: {claim.claim_text}")
                    print(f"  VERDICT: {claim.verdict}")
                    print(f"  REASONING: {claim.reasoning}")
        except Exception as e:
            print(f"Pipeline error on question {i+1}: {e}")

if __name__ == "__main__":
    main()
