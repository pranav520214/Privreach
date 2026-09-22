from pydantic import BaseModel, Field
from typing import List

class EvaluatedClaim(BaseModel):
    claim_text: str = Field(description="The specific factual claim extracted from the response")
    verdict: str = Field(description="Strictly 'SUPPORTED', 'CONTRADICTED', or 'UNSUPPORTED'")
    reasoning: str = Field(description="Brief explanation linking the verdict to the evidence")

class VerificationReport(BaseModel):
    claims: List[EvaluatedClaim] = Field(description="List of all evaluated claims")
    is_safe: bool = Field(description="True if ALL claims are SUPPORTED, False otherwise")
