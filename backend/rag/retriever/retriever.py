import httpx
import logging
from typing import Dict, Any, List
from backend.app.core.config import settings
from backend.rag.vectorstore.qdrant_store import qdrant_store

logger = logging.getLogger(__name__)

class RAGRetriever:
    def __init__(self):
        self.ollama_url = f"{settings.OLLAMA_BASE_URL}/api/generate"
        self.model_name = settings.OLLAMA_MODEL

    async def generate_answer(self, document_id: int, query: str) -> Dict[str, Any]:
        """
        Retrieves relevant document chunks and uses Ollama to answer the query.
        """
        # Step 1: Retrieve relevant chunks from Qdrant
        logger.info(f"Retrieving chunks for doc {document_id} and query: '{query}'")
        search_results = qdrant_store.search_chunks(document_id=document_id, query=query, limit=4)
        
        chunks = [res["chunk_text"] for res in search_results]
        
        if not chunks:
            # Fallback if no vector search results found
            context = "No specific document context found in vector store."
        else:
            context = "\n\n---\n\n".join(chunks)
            
        # Step 2: Build the prompt
        system_instruction = (
            "You are an expert AI Compliance Risk Copilot. Answer the user's question about the compliance "
            "document based strictly on the provided context extracted from the document. "
            "If the answer cannot be found or inferred from the context, state that clearly, "
            "but answer to the best of your ability using general compliance guidelines if helpful. "
            "Keep the answer professional, structured, and easy to read."
        )
        
        prompt = f"""{system_instruction}

DOCUMENT CONTEXT:
{context}

USER QUESTION:
{query}

ANSWER:"""

        # Step 3: Call Ollama API
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2  # low temperature for factuality
            }
        }
        
        try:
            logger.info(f"Sending request to Ollama ({self.model_name}) at {self.ollama_url}")
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(self.ollama_url, json=payload)
                
                if response.status_code != 200:
                    logger.error(f"Ollama returned status {response.status_code}: {response.text}")
                    return {
                        "answer": "Error: Failed to get response from local LLM service (Ollama).",
                        "retrieved_chunks": chunks
                    }
                    
                result = response.json()
                answer = result.get("response", "No response text received.")
                return {
                    "answer": answer.strip(),
                    "retrieved_chunks": chunks
                }
        except httpx.RequestError as exc:
            logger.error(f"HTTP Request to Ollama failed: {exc}")
            return {
                "answer": "Error: Ollama service is unreachable. Ensure 'ollama run llama3.1' is active.",
                "retrieved_chunks": chunks
            }
        except Exception as e:
            logger.error(f"Unexpected error in RAG retriever: {e}")
            return {
                "answer": f"Error: An unexpected error occurred: {str(e)}",
                "retrieved_chunks": chunks
            }

rag_retriever = RAGRetriever()
