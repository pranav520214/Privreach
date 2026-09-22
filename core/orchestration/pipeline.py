import sys
from pathlib import Path
from llama_cpp import Llama

sys.path.append(str(Path(__file__).parent.parent.parent))

from rlcd.router.query_analyzer import RLCDRouter
from knowledge.retrieval.hybrid_search import HybridRetriever
from rlcd.verifier.adversarial_verifier import AdversarialVerifier
from core.schemas.rlcd_schemas import ExecutionPlan, RiskLevel
from knowledge.ingestion.document_loader import DynamicDocumentLoader

class PrvaVedaPipeline:
    def __init__(self, synth_model_path: str, router_model_path: str, corpus_path: str):
        print("[SYSTEM] Loading 0.5B RLCD Router SLM into memory...")
        self.router_llm = Llama(
            model_path=router_model_path,
            n_ctx=2048,
            n_gpu_layers=0, # Keep fully on CPU to reserve VRAM
            verbose=False
        )
        
        print("[SYSTEM] Loading 4B Synthesis SLM into memory...")
        self.synth_llm = Llama(
            model_path=synth_model_path,
            n_ctx=8192,
            n_gpu_layers=10, 
            verbose=False
        )
        
        self.router = RLCDRouter(self.router_llm)
        self.verifier = AdversarialVerifier(self.router_llm) # Use tiny model for verification too!
        
        self.retriever = HybridRetriever(corpus_path)
        self.retriever_initialized = False
        
        self.doc_loader = DynamicDocumentLoader()
        
    def ingest_pdf(self, pdf_path: str):
        if not self.retriever_initialized:
            self.retriever.initialize()
            self.retriever_initialized = True
        
        print(f"\n[INGESTION] Extracting and processing PDF: {pdf_path}")
        chunks = self.doc_loader.process_pdf(pdf_path)
        self.retriever.ingest_chunks(chunks)
        print("[INGESTION] PDF successfully indexed in-memory.")
        return len(chunks)

    def _generate_response(self, query: str, evidence=None) -> str:
        context = evidence.to_prompt_context() if evidence else "No external evidence provided."
        
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
        
        output = self.synth_llm(
            prompt,
            max_tokens=512,
            temperature=0.1,
            stop=["<|im_end|>"],
            echo=False
        )
        return output['choices'][0]['text'].strip()
        
    def execute(self, query: str, stream_callback=None):
        def log(msg):
            if stream_callback:
                stream_callback(msg)
            else:
                print(msg)
                
        log("\n" + "="*60)
        log(f"PIPELINE INITIATED FOR QUERY:\n{query}")
        log("="*60)
        
        log("\n[RLCD] Analyzing query with ultra-fast 0.5B Router...")
        plan: ExecutionPlan = self.router.analyze_query(query)
        
        log("\n[RLCD] Execution Plan Generated:")
        log(f"  - Domain: {plan.domain}")
        log(f"  - Task Type: {plan.task_type.value}")
        log(f"  - Risk Level: {plan.risk_level.value}")
        log(f"  - Requires Retrieval: {plan.requires_retrieval}")
        log(f"  - Required Tools: {[t.value for t in plan.required_tools]}")
        
        evidence = None
        if plan.requires_retrieval:
            if not self.retriever_initialized:
                log("\n[KNOWLEDGE] Initializing Hybrid Retrieval System...")
                self.retriever.initialize()
                self.retriever_initialized = True
                
            log("\n[KNOWLEDGE] Retrieving evidence from local corpus...")
            evidence = self.retriever.search(query, top_k=3)
            log(f"  - Retrieved {len(evidence.chunks)} chunks.")
        
        log("\n[SLM] Generating candidate response with 4B Synthesis Model...")
        candidate = self._generate_response(query, evidence)
        
        if plan.risk_level in [RiskLevel.MEDIUM, RiskLevel.CRITICAL_RESEARCH] and evidence:
            log("\n[VERIFIER] Auditing claims with 0.5B Verifier...")
            report = self.verifier.verify(candidate, evidence)
            
            log(f"\n[VERIFIER] Audit Complete. Is Safe: {report.is_safe}")
            if not report.is_safe:
                log("\n[VERIFIER WARNING] The response contains unsupported claims!")
                return candidate, report, plan
                
        return candidate, None, plan
