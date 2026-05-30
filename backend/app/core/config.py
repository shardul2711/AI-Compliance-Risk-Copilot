import os
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Compliance Risk Copilot"
    API_V1_STR: str = "/api"
    
    # Database
    DATABASE_URL: str = Field(
        default="mysql+pymysql://root:Shardul%4027@localhost:3306/ai_compliance",
        description="MySQL Database connection URL"
    )
    
    # JWT Security
    SECRET_KEY: str = Field(
        default="super-secret-key-for-ai-compliance-risk-copilot-2026",
        description="Secret key for JWT generation"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    
    # Ollama LLM
    OLLAMA_BASE_URL: str = Field(
        default="http://localhost:11434",
        description="Base URL for local Ollama service"
    )
    OLLAMA_MODEL: str = Field(
        default="llama3.1:latest",
        description="Ollama model to use for analysis and chat"
    )
    
    # Embeddings
    EMBEDDING_MODEL_NAME: str = Field(
        default="BAAI/bge-small-en-v1.5",
        description="Sentence-transformer embedding model"
    )
    
    # Storage Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    UPLOAD_DIR: str = Field(
        default="",
        description="Directory to store uploaded PDF documents"
    )
    QDRANT_PATH: str = Field(
        default="",
        description="Local directory for Qdrant client storage"
    )

    model_config = {
        "env_file": ".env",
        "case_sensitive": True
    }

    def __init__(self, **values):
        super().__init__(**values)
        if not self.UPLOAD_DIR:
            self.UPLOAD_DIR = os.path.join(self.BASE_DIR, "uploads")
        if not self.QDRANT_PATH:
            self.QDRANT_PATH = os.path.join(self.BASE_DIR, "qdrant_db")
        
        # Ensure directories exist
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        os.makedirs(self.QDRANT_PATH, exist_ok=True)

settings = Settings()
