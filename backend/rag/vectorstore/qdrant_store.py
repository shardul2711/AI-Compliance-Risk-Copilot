from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from typing import List, Dict, Any
import logging
import uuid
from backend.app.core.config import settings
from backend.rag.embeddings.embedder import embedding_service

logger = logging.getLogger(__name__)

class QdrantStore:
    def __init__(self):
        self.collection_name = "compliance_document_chunks"
        self.client = None
        self._initialized = False

    def initialize(self):
        if self._initialized:
            return
            
        logger.info(f"Initializing Qdrant Client at: {settings.QDRANT_PATH}")
        # Connect to local Qdrant directory
        self.client = QdrantClient(path=settings.QDRANT_PATH)
        
        # Ensure collection exists
        # We use 384 dimensions which is standard for BAAI/bge-small-en-v1.5 and all-MiniLM-L6-v2
        vector_size = 384
        
        try:
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"Creating Qdrant collection: {self.collection_name} with dim={vector_size}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
                )
                logger.info(f"Collection '{self.collection_name}' created.")
            self._initialized = True
        except Exception as e:
            logger.error(f"Error initializing Qdrant collection: {e}")
            raise e

    def add_chunks(self, document_id: int, chunks: List[str]) -> bool:
        """
        Embeds list of text chunks and adds them to Qdrant collection with payload.
        """
        self.initialize()
        if not chunks:
            return False
            
        try:
            logger.info(f"Embedding {len(chunks)} chunks for document {document_id}...")
            embeddings = embedding_service.embed_documents(chunks)
            
            points = []
            for i, (chunk_text, vector) in enumerate(zip(chunks, embeddings)):
                # Qdrant requires a UUID or int for point ID. We generate a random UUID
                point_id = str(uuid.uuid4())
                points.append(
                    PointStruct(
                        id=point_id,
                        vector=vector,
                        payload={
                            "document_id": int(document_id),
                            "chunk_text": chunk_text,
                            "chunk_index": i
                        }
                    )
                )
                
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.info(f"Upserted {len(chunks)} chunks into Qdrant for document {document_id}.")
            return True
        except Exception as e:
            logger.error(f"Failed to upsert chunks to Qdrant: {e}")
            return False

    def search_chunks(self, document_id: int, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Searches for chunks relevant to the query, filtered by document_id.
        """
        self.initialize()
        try:
            query_vector = embedding_service.embed_query(query)
            
            # Filter specifically by document_id payload
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=int(document_id))
                    )
                ]
            )
            
            search_results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                query_filter=query_filter,
                limit=limit
            )
            
            results = []
            for hit in search_results.points:
                results.append({
                    "chunk_text": hit.payload.get("chunk_text"),
                    "chunk_index": hit.payload.get("chunk_index"),
                    "score": hit.score
                })
            return results
        except Exception as e:
            logger.error(f"Search failed in Qdrant: {e}")
            return []

    def delete_document_chunks(self, document_id: int) -> bool:
        """
        Deletes all vector points associated with a specific document.
        """
        self.initialize()
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=int(document_id))
                        )
                    ]
                )
            )
            logger.info(f"Deleted vector chunks for document {document_id}.")
            return True
        except Exception as e:
            logger.error(f"Failed to delete vector chunks for document {document_id}: {e}")
            return False

qdrant_store = QdrantStore()
