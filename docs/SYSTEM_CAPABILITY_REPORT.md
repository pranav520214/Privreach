# SYSTEM CAPABILITY REPORT

## 1. Hardware Overview
* **CPU**: AMD Ryzen 5 7600 6-Core Processor (12 Logical Processors)
* **RAM**: 16 GB Physical RAM
* **GPU**: NVIDIA GeForce GTX 1650
* **VRAM**: 4 GB

## 2. Storage
* **Drive C**: 297.48 GB Free (System Drive)
* **Drive D**: 134.37 GB Free
* **Drive E**: 204.34 GB Free (Primary Prva Veda storage)
* **Drive F**: 25.20 GB Free

## 3. Software Environment
* **Python**: 3.11.9 (64-bit)
* **PyTorch**: 2.13.0+cpu
* **CUDA**: **NOT AVAILABLE** to the current PyTorch installation. (This is a critical bottleneck for native Hugging Face model inference).

## 4. Locally Cached Models
Found multiple local GGUF and standard Hugging Face models in `~/.cache/huggingface/hub`:
* `Dolphin3.0-Llama3.1-8B-GGUF`
* `Cerberus-4B-GGUF`
* `Huihui-Qwen3.5-4B-abliterated-GGUF`
* `Marco-DeepResearch-8B-i1-GGUF`
* `Qwen/Qwen2.5-7B-Instruct`
* `Qwen/Qwen3-1.7B`
* `unsloth/Qwen2.5-Coder-3B-Instruct-bnb-4bit`

## 5. Architectural Implications & Hardware Bottlenecks
1. **GPU VRAM Constraint**: 4 GB VRAM is insufficient to run a 3B–8B parameter model entirely on the GPU in FP16 (which requires ~6-16 GB).
2. **PyTorch CPU Fallback**: The current PyTorch build does not have CUDA enabled. Any standard Hugging Face inference will run purely on the CPU, which is extremely slow.
3. **Recommendation (llama.cpp)**: To achieve usable inference speeds for the RLCD architecture and Foundational SLM, the system **must** use `llama.cpp` (e.g., via `llama-cpp-python`). This will allow loading the cached GGUF models (like `Dolphin3.0-Llama3.1-8B-GGUF` or `Huihui-Qwen3.5-4B`) with partial GPU offloading (offloading as many layers as fit into the 4GB VRAM) and CPU inference for the rest.
4. **Corpus Pipeline**: The dataset builder pipeline was previously implemented at `E:\Prva_Veda_Research_Library\dataset_builder`. It operates completely locally and requires no GPU, making it a perfect Phase 1 component.
