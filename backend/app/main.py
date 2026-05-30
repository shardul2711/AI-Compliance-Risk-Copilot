from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from backend.app.core.config import settings
from backend.app.api.auth import router as auth_router
from backend.app.api.documents import router as doc_router
from backend.app.api.audit import router as audit_router
from backend.app.services.ml_service import ml_service

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup sequence
    logger.info("Starting AI Compliance Risk Copilot Backend...")
    try:
        # Pre-warm ML models. It will auto-generate and auto-train if missing
        ml_service.initialize()
    except Exception as e:
        logger.warning(f"Could not warm up ML models on startup: {e}. They will be initialized on-demand.")
    yield
    # Shutdown sequence
    logger.info("Shutting down AI Compliance Risk Copilot Backend...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    version="1.0.0"
)

# CORS configuration
# Next.js usually runs on port 3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(doc_router, prefix=settings.API_V1_STR)
app.include_router(audit_router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    return {"message": "Welcome to the AI Compliance Risk Copilot API."}

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": settings.PROJECT_NAME}
