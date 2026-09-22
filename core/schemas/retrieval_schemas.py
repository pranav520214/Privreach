from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class RetrievedChunk(BaseModel):
    chunk_id: str = Field(description="Unique identifier for the chunk")
    document_id: str = Field(description="Unique identifier for the source document")
    text: str = Field(description="The scientific prose content")
    section: Optional[str] = Field(default=None, description="Section of the document (e.g., Methods)")
    title: Optional[str] = Field(default=None, description="Title of the source document")
    authors: Optional[List[str]] = Field(default=None, description="Authors of the document")
    year: Optional[int] = Field(default=None, description="Year of publication")
    score: float = Field(description="Relevance score from the retrieval system")
    retrieval_method: str = Field(description="Method used for retrieval (e.g., bm25, dense, hybrid)")

class EvidencePackage(BaseModel):
    query: str = Field(description="The original user query")
    domain: Optional[str] = Field(default=None, description="The classified domain for the query")
    chunks: List[RetrievedChunk] = Field(description="Ranked list of evidence chunks")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional retrieval metadata")
    
    def to_prompt_context(self) -> str:
        """
        Formats the evidence package into a string suitable for LLM context.
        """
        context_parts = []
        for i, chunk in enumerate(self.chunks):
            header = f"[Evidence {i+1}] Source: {chunk.title or 'Unknown'} (ID: {chunk.chunk_id})"
            if chunk.section:
                header += f" | Section: {chunk.section}"
            
            context_parts.append(f"{header}\n{chunk.text}\n")
            
        return "\n".join(context_parts)
