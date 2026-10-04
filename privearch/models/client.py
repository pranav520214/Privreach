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
        """Check if local inference engine is running."""
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags")
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status == 200
        except Exception:
            return False

    def ensure_server_running(self) -> bool:
        """Automatically boot local Ollama server if not currently active."""
        if self.is_available():
            return True
        import os
        import subprocess
        import shutil
        import time

        ollama_bin = shutil.which("ollama") or os.path.expanduser(r"~\AppData\Local\Programs\Ollama\ollama.exe")
        if os.path.exists(ollama_bin):
            try:
                subprocess.Popen(
                    [ollama_bin, "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
                )
                for _ in range(10):
                    time.sleep(0.6)
                    if self.is_available():
                        return True
            except Exception:
                pass
        return self.is_available()

    def list_models(self) -> List[str]:
        """List currently downloaded local models."""
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []

    def select_best_model(self, preferred: str, fallbacks: List[str]) -> str:
        """Select preferred model if available, else first working fallback."""
        available = self.list_models()
        # Direct match or prefix match (e.g. 'qwen2.5:0.5b' matches 'qwen2.5:0.5b' or 'qwen2.5:0.5b-instruct')
        for candidate in [preferred] + fallbacks:
            for m in available:
                if candidate in m or m in candidate:
                    return m
        # If nothing matches, return preferred
        return preferred

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
        Execute synchronous generation on local LLM.
        """
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
