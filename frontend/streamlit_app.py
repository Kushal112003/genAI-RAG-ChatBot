import os
import sys
import subprocess
from pathlib import Path

import requests
import streamlit as st

# Adjust path for backend imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.evaluation.ragas_eval import run_ragas_evaluation
from backend.database.stats import get_stats
from backend.ingestion.incremental_ingest import ingest_single_document
from backend.evaluation.metrics import get_metrics

# ==========================
# PAGE CONFIG
# ==========================
st.set_page_config(
    page_title="Engineering Knowledge Assistant",
    page_icon="🤖",
    layout="wide"
)

# ==========================
# SESSION STATE
# ==========================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "show_metrics" not in st.session_state:
    st.session_state.show_metrics = False

if "indexed_files" not in st.session_state:
    st.session_state.indexed_files = []

# ==========================
# SIDEBAR
# ==========================
with st.sidebar:
    st.title("⚙️ System Information")
    st.success("RAG Engine Active")

    # Analytics 
    stats = get_stats()
    st.metric("Documents", stats["documents"])
    st.metric("Chunks", stats["chunks"])
    
    st.markdown("---")

    if st.button("📊 Run RAGAS Evaluation"):
        with st.spinner("Running RAGAS Evaluation..."):
            run_ragas_evaluation()
            st.success("Evaluation Completed")
            
    if st.button("👁️ Show / Hide Evaluation"):
        st.session_state.show_metrics = not st.session_state.show_metrics

    if st.session_state.show_metrics:
        metrics = get_metrics()
        
        st.subheader("📊 RAG Evaluation")
        st.metric("Faithfulness", metrics["faithfulness"])
        st.metric("Answer Relevancy", metrics["answer_relevancy"])
        st.metric("Context Precision", metrics["context_precision"])
        st.metric("Context Recall", metrics["context_recall"])
        
        st.markdown(
            """
            ### Embedding Model
            all-MiniLM-L6-v2

            ### LLM
            llama-3.3-70b-versatile

            ### Vector Database
            ChromaDB

            ### Backend
            FastAPI

            ### Frontend
            Streamlit
            """
        )

    st.markdown("---")

    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")

# ==========================
# FILE UPLOADER
# ==========================
uploaded_file = st.file_uploader("Upload Document", type=["pdf", "docx", "txt"])

if uploaded_file:
    if uploaded_file.name not in st.session_state.indexed_files:
        save_path = Path("data") / uploaded_file.name

        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        with st.spinner("Indexing document..."):
            chunks = ingest_single_document(str(save_path))

        st.session_state.indexed_files.append(uploaded_file.name)
        st.success(f"{uploaded_file.name} indexed successfully!")
        st.info(f"Added {chunks} chunks to vector database.")

# ==========================
# MAIN PAGE
# ==========================
st.title("🤖 Engineering Knowledge Assistant")

st.markdown(
    """
    Ask questions about:
    - AWS
    - Kubernetes
    - Docker
    - Terraform
    - Linux
    - FastAPI
    - Pulumi

    The assistant answers using your uploaded engineering documentation.
    """
)

# ==========================
# REINDEX BUTTON
# ==========================
if st.button("🔄 Full Rebuild Knowledge Base"):
    with st.spinner("Rebuilding vector database..."):
        result = subprocess.run(
            [sys.executable, "-m", "backend.ingestion.pipeline"],
            capture_output=True,
            text=True
        )

    if result.returncode == 0:
        st.success("Knowledge Base Updated Successfully!")
        st.text(result.stdout)
    else:
        st.error("Reindexing Failed!")
        st.text(result.stderr)

# ==========================
# DISPLAY CHAT HISTORY
# ==========================
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ==========================
# CHAT INPUT
# ==========================
question = st.chat_input("Ask a technical question...")

# ==========================
# USER QUESTION
# ==========================
if question:
    # Store user message
    st.session_state.messages.append({"role": "user", "content": question})

    # Display user message
    with st.chat_message("user"):
        st.markdown(question)

    # Generate response
    with st.spinner("Searching engineering knowledge base..."):
        try:
            response = requests.post(
                "http://127.0.0.1:8000/chat",
                json={"question": question},
                timeout=120
            )
            result = response.json()
            answer = result["answer"]
            source = result["source"]
        except Exception as e:
            answer = f"Error: {str(e)}"
            source = []

    # Store assistant response
    st.session_state.messages.append({"role": "assistant", "content": answer})

    # Display assistant response
    with st.chat_message("assistant"):
        st.markdown(answer)
        if source:
            st.markdown("---")
            st.markdown("### 📚 Sources")
            for src in source:
                st.info(src)