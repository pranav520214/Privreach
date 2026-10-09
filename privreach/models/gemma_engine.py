"""In-Process Native Inference Engine for Google Gemma 3 1B IT.

Runs 100% offline and in-process using embedded llama_cpp (GGUF Q4_K_M).
Requires ZERO external servers, ZERO Ollama installation, and ZERO internet access.
"""

import os
import sys
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class GemmaInProcessEngine:
    _instance: Optional["GemmaInProcessEngine"] = None

    def __init__(self, model_path: Optional[str] = None, n_ctx: int = 4096, n_threads: Optional[int] = None):
        self.model_path = model_path or self.discover_model_path()
        self.n_ctx = n_ctx
        self.n_threads = n_threads or max(1, (os.cpu_count() or 4) - 1)
        self._llm = None

    @classmethod
    def get_instance(cls) -> "GemmaInProcessEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @staticmethod
    def discover_model_path() -> Optional[str]:
        """Search standard candidate locations for Gemma 3 1B GGUF weights."""
        candidates = [
            os.path.join(os.getcwd(), "models", "gemma-3-1b-it-q4_k_m.gguf"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "models", "gemma-3-1b-it-q4_k_m.gguf"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "gemma-3-1b-it-q4_k_m.gguf"),
            os.path.join(os.path.dirname(sys.executable), "models", "gemma-3-1b-it-q4_k_m.gguf"),
            os.path.join(os.path.dirname(sys.executable), "_internal", "models", "gemma-3-1b-it-q4_k_m.gguf"),
            os.path.join(getattr(sys, "_MEIPASS", ""), "models", "gemma-3-1b-it-q4_k_m.gguf"),
            os.path.join(os.path.dirname(sys.executable), "gemma-3-1b-it-q4_k_m.gguf"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Privreach", "models", "gemma-3-1b-it-q4_k_m.gguf"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Privreach", "Workstation", "models", "gemma-3-1b-it-q4_k_m.gguf"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Privreach", "Workstation", "privreach_engine", "models", "gemma-3-1b-it-q4_k_m.gguf"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Privreach", "Workstation", "privreach_engine", "_internal", "models", "gemma-3-1b-it-q4_k_m.gguf"),
        ]
        for p in candidates:
            abs_p = os.path.abspath(p)
            if os.path.exists(abs_p) and os.path.getsize(abs_p) > 10_000_000:
                return abs_p
        return None

    def is_available(self) -> bool:
        """Returns True if model weights exist and llama_cpp is importable."""
        if not self.model_path or not os.path.exists(self.model_path):
            self.model_path = self.discover_model_path()
        if not self.model_path or not os.path.exists(self.model_path):
            return False
        try:
            import llama_cpp
            return True
        except ImportError:
            return False

    def load_model(self):
        """Load GGUF model into memory."""
        if self._llm is not None:
            return self._llm
        if not self.is_available():
            raise RuntimeError(f"Gemma 3 1B IT weights not found at: {self.model_path}")

        from llama_cpp import Llama
        logger.info(f"Loading in-process Gemma 3 1B IT from {self.model_path} (threads={self.n_threads}, ctx={self.n_ctx})")
        self._llm = Llama(
            model_path=self.model_path,
            n_ctx=self.n_ctx,
            n_threads=self.n_threads,
            n_gpu_layers=0,  # Pure CPU leaves 100% VRAM free
            verbose=False
        )
        return self._llm

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        stop: Optional[List[str]] = None
    ) -> str:
        """Execute synchronous in-process generation using Google Gemma 3 1B IT."""
        llm = self.load_model()
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        stop_sequences = stop or ["<end_of_turn>", "<eos>"]

        output = llm.create_chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stop=stop_sequences
        )
        choice = output["choices"][0]["message"]
        content = choice.get("content", "") or ""
        return content.strip()

    def get_status(self) -> Dict[str, Any]:
        available = self.is_available()
        return {
            "engine": "in_process_gemma3",
            "model_name": "google/gemma-3-1b-it",
            "format": "GGUF Q4_K_M (768MB)",
            "available": available,
            "loaded": self._llm is not None,
            "threads": self.n_threads,
            "context_window": self.n_ctx,
            "weights_path": self.model_path
        }
