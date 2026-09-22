import pymupdf as fitz
import re
import uuid
from pathlib import Path

class DynamicDocumentLoader:
    def __init__(self, chunk_size: int = 500, overlap: int = 100):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def process_pdf(self, pdf_path: str) -> list[dict]:
        """
        Extracts text from a PDF, chunks it, and returns a list of dictionaries
        matching the corpus schema.
        """
        doc = fitz.open(pdf_path)
        doc_id = str(uuid.uuid4())
        title = doc.metadata.get("title", Path(pdf_path).name) if hasattr(Path, 'name') else "Uploaded Document"
        
        full_text = ""
        for page in doc:
            full_text += page.get_text() + "\n"
            
        doc.close()
        
        # Clean text
        text = re.sub(r'\s+', ' ', full_text).strip()
        
        # Simple word-based chunking
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), self.chunk_size - self.overlap):
            chunk_words = words[i:i + self.chunk_size]
            if not chunk_words:
                break
                
            chunk_text = " ".join(chunk_words)
            chunks.append({
                "id": str(uuid.uuid4()),
                "document_id": doc_id,
                "title": title,
                "text": chunk_text,
                "year": 2026, # Default
                "authors": ["Dynamic Upload"]
            })
            
        return chunks
