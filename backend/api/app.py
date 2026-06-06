"""
Enterprise Knowledge Assistant — FastAPI Application
=====================================================
Production-grade REST API with proper router separation,
CORS middleware, and health checks.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from backend.api.routes.chat import router as chat_router
from backend.api.routes.upload import router as upload_router
from backend.api.routes.analytics import router as analytics_router

# ──────────────────────────────────────────────
# Application
# ──────────────────────────────────────────────

app = FastAPI(
    title="Enterprise Knowledge Assistant API",
    description=(
        "A production-grade RAG API that supports multi-domain document "
        "retrieval (Engineering & Company Policies), multi-LLM providers, "
        "and RAGAS-based evaluation."
    ),
    version="2.0.0",
)

# ──────────────────────────────────────────────
# Middleware
# ──────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────
# Routers
# ──────────────────────────────────────────────

app.include_router(chat_router)
app.include_router(upload_router)
app.include_router(analytics_router)

# ──────────────────────────────────────────────
# Root & Health
# ──────────────────────────────────────────────


@app.get("/", tags=["System"])
async def root():
    return {
        "service": "Enterprise Knowledge Assistant API",
        "version": "2.0.0",
        "status": "running",
    }


@app.get("/health", tags=["System"])
async def health():
    return {"status": "healthy"}
