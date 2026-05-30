from sentence_transformers import SentenceTransformer
from typing import List
import os
import logging
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.model_name = settings.EMBEDDING_MODEL_NAME
        self.model = None

    def load_model(self):
        if self.model is None:
            logger.info(f"Loading local SentenceTransformer model: {self.model_name}...")
            # This downloads and loads the model locally. It is cached in standard huggingface cache.
            self.model = SentenceTransformer(self.model_name)
            logger.info("SentenceTransformer model loaded successfully.")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        self.load_model()
        embeddings = self.model.encode(texts, show_progress_bar=False)
        return [emb.tolist() for emb in embeddings]

    def embed_query(self, text: str) -> List[float]:
        self.load_model()
        embedding = self.model.encode(text, show_progress_bar=False)
        return embedding.tolist()

embedding_service = EmbeddingService()
