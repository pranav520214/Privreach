import json
from typing import Dict, Any
from llama_cpp import Llama
from core.schemas.verification_schemas import VerificationReport
from core.schemas.retrieval_schemas import EvidencePackage

class AdversarialVerifier:
    def __init__(self, llm: Llama):
        # We share the LLM instance to avoid loading multiple models in memory
        self.llm = llm
        
    def verify(self, candidate_response: str, evidence: EvidencePackage) -> VerificationReport:
        """
        Forces the LLM to dissect its own response into claims and verify them against the evidence.
        """
        schema = VerificationReport.model_json_schema()
        
        system_prompt = (
            "You are the Prva Veda Adversarial Verifier. Your job is to audit a candidate response "
            "against the provided scientific evidence. You must extract every factual claim from the "
            "response and rigorously evaluate if it is SUPPORTED, CONTRADICTED, or UNSUPPORTED by the evidence. "
            "Output your findings STRICTLY as a JSON object matching the provided schema."
        )
        
        context = evidence.to_prompt_context() if evidence else "No external evidence provided."
        
        user_prompt = f"""
EVIDENCE:
{context}

CANDIDATE RESPONSE TO AUDIT:
{candidate_response}
"""
        
        response = self.llm.create_chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={
                "type": "json_object",
                "schema": schema
            },
            temperature=0.0,
            max_tokens=1024
        )
        
        json_str = response["choices"][0]["message"]["content"]
        
        try:
            report_dict = json.loads(json_str)
            report = VerificationReport(**report_dict)
            return report
        except Exception as e:
            print(f"Failed to parse Verifier output: {json_str}")
            # Fallback to an unsafe report if parsing completely fails
            return VerificationReport(claims=[], is_safe=False)
