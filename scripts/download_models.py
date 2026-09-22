from huggingface_hub import hf_hub_download

def download_models():
    print("Downloading/Verifying 4B Synthesis Model...")
    synth_path = hf_hub_download(
        repo_id="mradermacher/Huihui-Qwen3.5-4B-abliterated-GGUF",
        filename="Huihui-Qwen3.5-4B-abliterated.Q4_K_M.gguf"
    )
    print(f"Synthesis Model Path: {synth_path}")
    
    print("Downloading/Verifying 0.5B Router Model...")
    router_path = hf_hub_download(
        repo_id="Qwen/Qwen2.5-0.5B-Instruct-GGUF",
        filename="qwen2.5-0.5b-instruct-q4_k_m.gguf"
    )
    print(f"Router Model Path: {router_path}")
    
    return router_path, synth_path

if __name__ == "__main__":
    download_models()
