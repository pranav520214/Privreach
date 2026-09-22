import streamlit as st
import tempfile
import os
from huggingface_hub import hf_hub_download
from core.orchestration.pipeline import PrvaVedaPipeline

st.set_page_config(page_title="Prva Veda", page_icon="🧬", layout="wide")

@st.cache_resource
def load_system():
    corpus_path = r"E:\Prva_Veda_Research_Library\datasets\retrieval\chunks.jsonl"
    
    with st.spinner("Downloading/Locating 4B Synthesis Model..."):
        synth_path = hf_hub_download(repo_id="mradermacher/Huihui-Qwen3.5-4B-abliterated-GGUF", filename="Huihui-Qwen3.5-4B-abliterated.Q4_K_M.gguf")
        
    with st.spinner("Downloading/Locating 0.5B Router Model..."):
        router_path = hf_hub_download(repo_id="Qwen/Qwen2.5-0.5B-Instruct-GGUF", filename="qwen2.5-0.5b-instruct-q4_k_m.gguf")
        
    with st.spinner("Initializing Dual-Model RLCD Pipeline..."):
        pipeline = PrvaVedaPipeline(synth_model_path=synth_path, router_model_path=router_path, corpus_path=corpus_path)
        
    return pipeline

st.title("Prva Veda - Scientific Assistant")
st.markdown("**(Phase 8: Universal Dual-Model Architecture)**")

pipeline = load_system()

# Sidebar for PDF Ingestion
with st.sidebar:
    st.header("Dynamic Knowledge Base")
    uploaded_file = st.file_uploader("Drop a new PDF to ingest", type="pdf")
    if uploaded_file is not None:
        with st.spinner("Ingesting PDF..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            
            chunks_added = pipeline.ingest_pdf(tmp_path)
            st.success(f"Added {chunks_added} chunks to memory!")
            os.remove(tmp_path)

# Chat Interface
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "report" in msg and msg["report"] and not msg["report"].is_safe:
            st.error("⚠️ Adversarial Verifier caught unsupported claims!")
            for claim in msg["report"].claims:
                if claim.verdict != "SUPPORTED":
                    st.write(f"**Claim:** {claim.claim_text} | **Verdict:** {claim.verdict}")

if prompt := st.chat_input("Ask a clinical pharmacokinetics question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("RLCD Routing & Synthesis..."):
            # Execute Pipeline
            candidate, report, plan = pipeline.execute(prompt)
            
            st.markdown(candidate)
            
            if report and not report.is_safe:
                st.error("⚠️ Adversarial Verifier caught unsupported claims!")
                for claim in report.claims:
                    if claim.verdict != "SUPPORTED":
                        st.write(f"**Claim:** {claim.claim_text} | **Verdict:** {claim.verdict}")
                        
        st.session_state.messages.append({"role": "assistant", "content": candidate, "report": report})
