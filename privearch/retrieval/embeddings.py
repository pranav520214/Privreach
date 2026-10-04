"""Zero-Trust local embedding engines for CPU vectorization."""

import json
import urllib.request
from typing import List
import numpy as np


class BaseEmbeddingEngine:
    def embed_documents(self, texts: List[str]) -> np.ndarray:
        raise NotImplementedError

    def embed_query(self, text: str) -> np.ndarray:
        raise NotImplementedError


class CpuTransformerEmbeddings(BaseEmbeddingEngine):
    """
    100% Local CPU Embeddings via sentence-transformers/all-MiniLM-L6-v2.
    Leaves 100% of 4GB VRAM free for the dual LLM brain-trust.
    """
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        import torch
        from transformers import AutoTokenizer, AutoModel

        self.model_name = model_name
        self.device = "cpu"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(self.device)
        self.model.eval()

    def _mean_pooling(self, model_output, attention_mask):
        import torch
        token_embeddings = model_output.last_hidden_state
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
        sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
        return sum_embeddings / sum_mask

    def embed_documents(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        import torch

        if not texts:
            return np.empty((0, 384), dtype=np.float32)

        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            inputs = self.tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt"
            ).to(self.device)

            with torch.no_grad():
                outputs = self.model(**inputs)
                embeddings = self._mean_pooling(outputs, inputs["attention_mask"])
                # L2 normalize
                embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
                all_embeddings.append(embeddings.cpu().numpy())

        return np.vstack(all_embeddings).astype(np.float32)

    def embed_query(self, text: str) -> np.ndarray:
        res = self.embed_documents([text])
        return res[0]


class OllamaEmbeddings(BaseEmbeddingEngine):
    """Local embeddings via Ollama embedding API."""
    def __init__(self, model_name: str = "qwen3-embedding:0.6b", base_url: str = "http://127.0.0.1:11434"):
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")

    def _call_embed(self, text: str) -> List[float]:
        url = f"{self.base_url}/api/embeddings"
        payload = json.dumps({"model": self.model_name, "prompt": text}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("embedding", [])

    def embed_documents(self, texts: List[str]) -> np.ndarray:
        vectors = []
        for t in texts:
            vec = self._call_embed(t)
            vectors.append(vec)
        arr = np.array(vectors, dtype=np.float32)
        # Normalize
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        norms[norms == 0] = 1e-9
        return arr / norms

    def embed_query(self, text: str) -> np.ndarray:
        vec = np.array(self._call_embed(text), dtype=np.float32)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec


def get_embedding_engine(backend: str = "cpu_minilm", **kwargs) -> BaseEmbeddingEngine:
    if backend == "ollama":
        return OllamaEmbeddings(
            model_name=kwargs.get("model_name", "qwen3-embedding:0.6b"),
            base_url=kwargs.get("base_url", "http://127.0.0.1:11434")
        )
    return CpuTransformerEmbeddings(
        model_name=kwargs.get("model_name", "sentence-transformers/all-MiniLM-L6-v2")
    )
