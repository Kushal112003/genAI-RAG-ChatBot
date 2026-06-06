# 🤖 Enterprise 2-in-1 RAG Platform

A production-grade **Retrieval-Augmented Generation (RAG)** system that serves as a 2-in-1 platform for both **Engineering Knowledge** and **Company Policy** queries. Built with industry-standard architecture patterns.

---

## 📖 What is RAG? (Theory & Reading)

**Retrieval-Augmented Generation (RAG)** is an AI framework that improves the quality of LLM-generated responses by grounding the model on external sources of knowledge.

Instead of relying solely on what an LLM memorized during training, RAG introduces a retrieval step:
1. **Index**: Your private documents are split into chunks, converted into mathematical vectors (Embeddings), and stored in a Vector Database.
2. **Retrieve**: When a user asks a question, the system searches the database for the most relevant document chunks.
3. **Generate**: The system passes the user's question AND the retrieved chunks to the LLM, instructing it to answer *only* using the provided context.

### 📚 Recommended Reading
- [Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks (Original Paper)](https://arxiv.org/abs/2005.11401)
- [IBM: What is RAG?](https://research.ibm.com/blog/retrieval-augmented-generation-RAG)
- [Pinecone: RAG Explained](https://www.pinecone.io/learn/retrieval-augmented-generation/)
- [RAGAS: Evaluating RAG Pipelines](https://docs.ragas.io/en/stable/)

---

## 🛠️ Tools & Libraries Used

This platform uses a modern, open-source stack designed for speed, cost-efficiency, and modularity:

| Library / Tool | Purpose & Use Case |
|---|---|
| **Streamlit** | **Frontend UI**. Builds the interactive chat interface, sidebar, and file uploader quickly without needing a separate React/Vue frontend. |
| **FastAPI** | **Backend API**. Provides blazing-fast REST endpoints (`/chat`, `/upload`, `/analytics`) for the frontend to communicate with. Handles streaming responses efficiently. |
| **ChromaDB** | **Vector Database**. An open-source, local database that stores document chunks and their semantic vectors. Performs blazing-fast similarity searches (HNSW indexing). |
| **HuggingFace (`all-MiniLM-L6-v2`)** | **Embedding Model**. Runs locally via ONNX to convert text into vectors. Chosen because it is extremely fast, free, and runs well on CPUs without needing expensive GPU cloud hosting. |
| **Groq API** | **LLM Provider**. Hosts open-source models like LLaMA 3.3. Groq uses custom LPUs (Language Processing Units) that generate tokens at incredible speeds, making the chat feel instantaneous. |
| **RAGAS** | **Evaluation Framework**. Uses "LLM-as-a-judge" to automatically score how good the RAG system is. It checks if answers are faithful to the text and relevant to the question. |
| **Uvicorn** | **ASGI Web Server**. Runs the FastAPI backend in production mode. |

---

## 🏗️ System Architecture

```text
┌─────────────────────────────────────────────────────────┐
│                    Streamlit Frontend                    │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Chat UI  │  │ File Upload  │  │ RAGAS Evaluation  │  │
│  │          │  │ + Domain Tag │  │    Dashboard      │  │
│  └──────────┘  └──────────────┘  └──────────────────┘  │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTP (REST API)
┌───────────────────────▼─────────────────────────────────┐
│                    FastAPI Backend                        │
│  ┌──────────────────────────────────────────────────┐   │
│  │              Query Context Router                 │   │
│  │         engineering ◄──► policy                    │   │
│  └──────────────────┬───────────────────────────────┘   │
│  ┌──────────────────▼───────────────────────────────┐   │
│  │           Retriever (Domain-Filtered)             │   │
│  │     ChromaDB Vector Search + BM25 Hybrid          │   │
│  └──────────────────┬───────────────────────────────┘   │
│  ┌──────────────────▼───────────────────────────────┐   │
│  │         LLM Provider Registry                     │   │
│  │    Groq  │  OpenAI  │  (Extensible)               │   │
│  └──────────────────┬───────────────────────────────┘   │
│  ┌──────────────────▼───────────────────────────────┐   │
│  │      Generator (Streaming + Citation Parsing)     │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## ✨ Enterprise Features

| Feature | Description |
|---|---|
| **2-in-1 Domain Isolation** | True separation of Engineering Knowledge and Company Policies. The UI lets you select a context, and the DB strictly filters (`where={"domain": "policy"}`) to prevent data bleed. |
| **Dynamic Personas** | The system prompt completely changes based on the selected domain (e.g., "Senior Cloud Engineer" vs "HR Policy Expert"). |
| **Batched Upsert Ingestion** | Documents are chunked and MD5-hashed. We use batched `upsert` to elegantly prevent database corruption and deduplicate uploads. |
| **Strict Citations** | Only documents actually used by the LLM appear in the Sources section. |
| **Hybrid Search (RRF)** | Combines BM25 keyword search with semantic vector search via Reciprocal Rank Fusion for maximum accuracy. |
| **RAGAS Evaluation** | Built-in LLM-as-a-Judge evaluation (Faithfulness, Answer Relevancy, Context Precision, Context Recall). |
| **Telemetry & Analytics** | Tracks query latency, domains, and user feedback (Thumbs up/down) in a local SQLite DB. |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- A Groq API key ([get one here](https://console.groq.com/keys))

### Installation

```bash
# Clone the repository
git clone https://github.com/Kushal112003/genAI-RAG-ChatBot.git
cd genAI-RAG-ChatBot

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
# Edit .env and add your API keys
```

### Running the Platform

You need to start both the Backend (FastAPI) and the Frontend (Streamlit).

```bash
# Terminal 1: Start the backend
uvicorn backend.api.app:app --host 127.0.0.1 --port 8000

# Terminal 2: Start the frontend
streamlit run frontend/streamlit_app.py --server.fileWatcherType none
```

Open `http://localhost:8501` in your browser.

### Docker Support

```bash
docker-compose up --build
```

---

## 🔌 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Service info |
| `GET` | `/health` | Health check |
| `POST` | `/chat` | Stream a chat response |
| `DELETE` | `/history` | Clear conversation memory |
| `POST` | `/upload` | Upload and ingest a document |
| `DELETE` | `/documents/{filename}` | Soft-delete a document |
| `DELETE` | `/documents/all/clear` | Wipe entire vector database |
| `GET` | `/analytics/telemetry` | System tracking stats |
| `GET` | `/analytics/documents` | Get list of indexed documents |

Full interactive Swagger documentation is available at `http://localhost:8000/docs`.

---

## 📄 License

MIT License
