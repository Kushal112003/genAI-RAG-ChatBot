"""
Enterprise Knowledge Assistant — Streamlit Frontend
=====================================================
Production-grade UI with multi-LLM provider selection,
document domain tagging, RAGAS evaluation, and streaming chat.
"""

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
from backend.rag.llm_providers import (
    get_available_providers,
    get_all_provider_names,
    validate_provider,
)

# ==========================
# PAGE CONFIG
# ==========================
st.set_page_config(
    page_title="Enterprise Knowledge Assistant",
    page_icon="🤖",
    layout="wide",
)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    
    .stApp {
        background-color: #0b0f19;
        color: #e2e8f0;
        font-family: 'Inter', sans-serif;
    }
    [data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.8) !important;
        backdrop-filter: blur(12px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    h1, h2, h3 {
        color: #38bdf8 !important;
        font-weight: 600;
        letter-spacing: -0.02em;
    }
    .stButton>button {
        background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%);
        color: white;
        border: none;
        border-radius: 8px;
        transition: all 0.2s ease;
        font-weight: 600;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(14, 165, 233, 0.4);
        color: white;
    }
    .stMetric {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 15px;
        border-radius: 10px;
        backdrop-filter: blur(5px);
    }
    </style>
""", unsafe_allow_html=True)

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

    # ── LLM Provider Selector ───────────────
    st.markdown("---")
    st.subheader("🧠 LLM Provider")

    all_providers = get_all_provider_names()
    available_providers = get_available_providers()

    selected_provider = st.selectbox(
        "Select LLM",
        all_providers,
        index=0,
        help="Only providers with a valid API key in .env will work.",
    )

    # Validate and show status
    is_valid, error_msg = validate_provider(selected_provider)
    if is_valid:
        st.success(f"✅ {selected_provider} — Key configured")
    else:
        st.error(f"🔑 Key not present for {selected_provider}")
        st.caption(f"Set the API key in your `.env` file.")

    # ── Analytics ───────────────────────────
    st.markdown("---")
    stats = get_stats()
    st.metric("Documents", stats["documents"])
    st.metric("Chunks", stats["chunks"])

    st.markdown("---")
    st.subheader("📈 Telemetry")
    try:
        telemetry_response = requests.get("http://127.0.0.1:8000/analytics/telemetry", timeout=2)
        if telemetry_response.ok:
            t_stats = telemetry_response.json()
            col1, col2 = st.columns(2)
            col1.metric("Queries", t_stats["total_queries"])
            col2.metric("Avg Latency", f"{t_stats['avg_response_time_ms']}ms")
            
            col3, col4 = st.columns(2)
            col3.metric("👍 Up", t_stats["thumbs_up"])
            col4.metric("👎 Down", t_stats["thumbs_down"])
    except:
        st.caption("Telemetry DB not initialized yet.")
        
    st.markdown("---")

    # ── RAGAS Evaluation ────────────────────
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

            ### Vector Database
            ChromaDB

            ### Backend
            FastAPI

            ### Frontend
            Streamlit

            ### Features
            - Multi-LLM Provider Support
            - Query Routing (Engineering / Policy)
            - Strict Citation Parsing
            - Hybrid Search (BM25 + Semantic)
            """
        )

    st.markdown("---")

    # ── Clear Chat ──────────────────────────
    if st.button("🗑️ Clear Chat"):
        try:
            requests.delete("http://127.0.0.1:8000/history", timeout=5)
        except Exception as e:
            st.error(f"Failed to clear backend history: {e}")
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")

# ==========================
# FILE UPLOADER
# ==========================
uploaded_file = st.file_uploader("Upload Document", type=["pdf", "docx", "txt"])

document_domain = st.selectbox(
    "📂 Document Category",
    ["Engineering Knowledge", "Company Policy"],
    help="Choose the category so the assistant only searches relevant documents.",
)

if uploaded_file:
    if uploaded_file.name not in st.session_state.indexed_files:
        save_path = Path("data") / uploaded_file.name

        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Map the friendly name to the domain ID
        domain_id = "engineering" if document_domain == "Engineering Knowledge" else "policy"

        with st.spinner("Indexing document..."):
            chunks = ingest_single_document(str(save_path), domain=domain_id)

        st.session_state.indexed_files.append(uploaded_file.name)
        st.success(f"✅ {uploaded_file.name} indexed as **{document_domain}**!")
        st.info(f"Added {chunks} chunks to vector database.")

# ==========================
# MAIN PAGE
# ==========================
st.title("🤖 Enterprise Knowledge Assistant")

st.markdown(
    """
    Ask questions about:
    - ☁️ **Engineering** — AWS, Kubernetes, Docker, Terraform, Linux, FastAPI, Pulumi
    - 📋 **Company Policies** — HR, Leave, Conduct, Benefits, Compliance

    The assistant automatically detects your intent and searches only the relevant documents.
    """
)

# ==========================
# DOCUMENT MANAGEMENT
# ==========================
st.markdown("---")
st.subheader("📚 Document Management")

try:
    doc_response = requests.get("http://127.0.0.1:8000/analytics/documents", timeout=2)
    if doc_response.ok:
        docs = doc_response.json().get("documents", [])
        if docs:
            for doc in docs:
                col1, col2, col3 = st.columns([3, 1, 1])
                col1.text(f"📄 {doc['filename']}")
                col2.caption(f"{doc['domain']} ({doc['chunk_count']} chunks)")
                
                if col3.button("Delete", key=f"del_{doc['filename']}", type="primary"):
                    with st.spinner(f"Deleting {doc['filename']}..."):
                        del_res = requests.delete(f"http://127.0.0.1:8000/documents/{doc['filename']}", timeout=10)
                        if del_res.ok:
                            st.success(f"Deleted {doc['filename']}")
                            # Remove from indexed files so it can be re-uploaded
                            if doc['filename'] in st.session_state.indexed_files:
                                st.session_state.indexed_files.remove(doc['filename'])
                            st.rerun()
                        else:
                            st.error(f"Failed to delete {doc['filename']}")
        else:
            st.info("No documents currently indexed.")
except Exception as e:
    st.error("Could not fetch document list. Is the backend running?")

st.markdown("---")
col_rebuild, col_wipe = st.columns(2)

with col_rebuild:
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
            st.rerun()
        else:
            st.error("Reindexing Failed!")
            st.text(result.stderr)

with col_wipe:
    if st.button("⚠️ Wipe Entire Database", type="primary"):
        with st.spinner("Wiping vector database and files..."):
            try:
                res = requests.delete("http://127.0.0.1:8000/documents/all/clear", timeout=30)
                if res.ok:
                    data = res.json()
                    st.success(f"Wiped! Deleted {data.get('chunks_deleted')} chunks and {data.get('files_deleted')} files.")
                    st.session_state.indexed_files = []
                    st.rerun()
                else:
                    st.error("Failed to wipe database.")
            except Exception as e:
                st.error(f"Error wiping database: {e}")

# ==========================
# DISPLAY CHAT HISTORY
# ==========================
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            st.markdown("---")
            st.markdown("### 📚 Sources")
            for src in message["sources"]:
                st.info(src)
        
        # Display feedback buttons for assistant responses
        if message["role"] == "assistant" and message.get("query_id"):
            feedback = st.feedback("thumbs", key=f"fb_{i}_{message['query_id']}")
            if feedback is not None and not message.get("feedback_submitted"):
                feedback_type = "up" if feedback == 1 else "down"
                try:
                    requests.post(
                        "http://127.0.0.1:8000/analytics/feedback",
                        json={"query_id": message["query_id"], "feedback_type": feedback_type},
                        timeout=2
                    )
                    st.session_state.messages[i]["feedback_submitted"] = True
                    st.toast("Thank you for your feedback!")
                except Exception as e:
                    st.error(f"Could not submit feedback: {e}")

# ==========================
# CHAT CONTEXT
# ==========================
chat_context = st.selectbox(
    "💬 Select Chat Context",
    ["Auto-Detect", "Engineering Knowledge Base", "Company Policy"],
    help="Choose whether to auto-detect the topic or force the assistant to use a specific knowledge base."
)

# ==========================
# CHAT INPUT
# ==========================
question = st.chat_input("Ask a question...")

# ==========================
# USER QUESTION
# ==========================
if question:
    # Check if the selected provider has a valid key
    is_valid, error_msg = validate_provider(selected_provider)
    if not is_valid:
        st.error(f"🔑 **API Key Not Present** — Cannot use {selected_provider}.\n\n"
                 f"Please set the required API key in your `.env` file or select a different provider from the sidebar.")
    else:
        # Store user message
        st.session_state.messages.append({"role": "user", "content": question})

        # Display user message
        with st.chat_message("user"):
            st.markdown(question)

        # Generate and stream response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            sources = []

            try:
                with requests.post(
                    "http://127.0.0.1:8000/chat",
                    json={
                        "question": question,
                        "provider": selected_provider,
                        "context_override": chat_context,
                    },
                    stream=True,
                    timeout=120
                ) as response:
                    import json
                    for line in response.iter_lines():
                        if line:
                            data = json.loads(line.decode('utf-8'))
                            if data["type"] == "token":
                                full_response += data["content"]
                                message_placeholder.markdown(full_response + "▌")
                            elif data["type"] == "sources":
                                sources = data["content"]
                                query_id = data.get("query_id")
                            elif data["type"] == "error":
                                full_response = f"⚠️ {data['content']}"
                                message_placeholder.markdown(full_response)

                if not full_response.startswith("⚠️"):
                    message_placeholder.markdown(full_response)

                if sources:
                    st.markdown("---")
                    st.markdown("### 📚 Sources")
                    for src in sources:
                        st.info(src)

            except Exception as e:
                full_response = f"Error: {str(e)}"
                message_placeholder.markdown(full_response)

        # Store assistant response
        st.session_state.messages.append({
            "role": "assistant",
            "content": full_response,
            "sources": sources,
            "query_id": locals().get("query_id"),
            "feedback_submitted": False
        })