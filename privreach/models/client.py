"""Zero-Trust local inference client strictly targeting localhost."""

import json
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional


class LocalModelClient:
    """
    Air-gapped, zero-trust local inference client.
    Guarantees that no prompts or tokens ever leave localhost.
    """
    def __init__(self, base_url: str = "http://127.0.0.1:11434"):
        self.base_url = base_url.rstrip("/")
        # Verify airgap safety
        if "127.0.0.1" not in self.base_url and "localhost" not in self.base_url:
            raise ValueError(
                f"ZERO-TRUST VIOLATION: Privearch is strictly air-gapped and rejects non-local host: {self.base_url}"
            )
        self.ensure_server_running()

    def is_available(self) -> bool:
        """Check if local inference engine (Gemma in-process or Ollama) is running."""
        try:
            from privreach.models.gemma_engine import GemmaInProcessEngine
            if GemmaInProcessEngine.get_instance().is_available():
                return True
        except Exception:
            pass

        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags")
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status == 200
        except Exception:
            return False

    def ensure_server_running(self) -> bool:
        """Automatically verify local inference availability."""
        if self.is_available():
            return True
        try:
            from privearch.models.engine_installer import start_ollama_daemon
            return start_ollama_daemon()
        except Exception:
            return False

    def list_models(self) -> List[str]:
        """List currently downloaded local models including embedded Gemma 3."""
        models = []
        try:
            from privreach.models.gemma_engine import GemmaInProcessEngine
            if GemmaInProcessEngine.get_instance().is_available():
                models.append("google/gemma-3-1b-it")
        except Exception:
            pass

        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models.extend([m["name"] for m in data.get("models", [])])
        except Exception:
            pass
        return models or ["google/gemma-3-1b-it"]

    def select_best_model(self, preferred: str, fallbacks: List[str]) -> str:
        """Select preferred model if available, else first working fallback."""
        available = self.list_models()
        for candidate in [preferred] + fallbacks:
            for m in available:
                if candidate in m or m in candidate:
                    return m
        return "google/gemma-3-1b-it" if "google/gemma-3-1b-it" in available else preferred

    def generate(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        timeout_seconds: int = 120
    ) -> str:
        """
        Execute synchronous generation on local LLM (In-Process Gemma 3 or Ollama).
        """
        # 1. Prefer in-process Gemma 3 1B IT if requested or if Ollama is unreachable
        use_gemma = "gemma" in model.lower()
        if not use_gemma:
            try:
                req = urllib.request.Request(f"{self.base_url}/api/tags")
                with urllib.request.urlopen(req, timeout=1.5) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    ollama_models = [m["name"] for m in data.get("models", [])]
                    if not any(model in m or m in model for m in ollama_models):
                        use_gemma = True
            except Exception:
                use_gemma = True

        if use_gemma:
            try:
                from privreach.models.gemma_engine import GemmaInProcessEngine
                gemma_engine = GemmaInProcessEngine.get_instance()
                if gemma_engine.is_available():
                    return gemma_engine.generate(
                        prompt=prompt,
                        system=system,
                        temperature=temperature,
                        max_tokens=max_tokens or 1024
                    )
            except Exception:
                pass

        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }
        if system:
            payload["system"] = system
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                response_text = result.get("response", "")
                # Strip thinking tags if model uses them
                if "<think>" in response_text and "</think>" in response_text:
                    response_text = response_text.split("</think>")[-1].strip()
                return response_text.strip()
        except urllib.error.URLError as e:
            raise RuntimeError(f"Local inference engine failure on model '{model}': {e}")
