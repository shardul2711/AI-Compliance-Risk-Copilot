import pypdf
import os
import re
from typing import List, Tuple
from sqlalchemy.orm import Session
from backend.app.models.models import Document, DocumentChunk
from backend.rag.vectorstore.qdrant_store import qdrant_store
import logging

logger = logging.getLogger(__name__)

class PDFService:
    def extract_text(self, file_path: str) -> str:
        """Extract text from PDF file using PyPDF."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found at {file_path}")
            
        logger.info(f"Extracting text from PDF: {file_path}")
        text = ""
        try:
            with open(file_path, "rb") as f:
                reader = pypdf.PdfReader(f)
                num_pages = len(reader.pages)
                logger.info(f"PDF has {num_pages} pages.")
                for page_num in range(num_pages):
                    page = reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            logger.error(f"Error during PDF extraction: {e}")
            raise e
            
        return text

    def clean_text(self, text: str) -> str:
        """Clean extracted text from double whitespaces and unreadable elements."""
        # Replace multiple spaces/newlines with single ones
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n+', '\n', text)
        text = text.strip()
        return text

    def chunk_text(self, text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks of a given character size."""
        chunks = []
        if not text:
            return chunks
            
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            
            # Move start forward by (chunk_size - chunk_overlap)
            start += (chunk_size - chunk_overlap)
            
            # Avoid infinite loop if overlap is larger than size
            if chunk_overlap >= chunk_size:
                break
                
        return chunks

    def process_document(self, db: Session, document_id: int) -> Tuple[bool, str]:
        """
        Executes the full pipeline:
        1. Extract text
        2. Clean text
        3. Chunk text
        4. Save to relational DB
        5. Embed and save to Qdrant Vector Store
        """
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return False, "Document not found in database."
            
        try:
            # Update status to processing
            doc.status = "Processing"
            db.commit()
            
            # Extract
            raw_text = self.extract_text(doc.file_path)
            if not raw_text:
                raise ValueError("Extracted text is empty.")
                
            # Clean
            cleaned_text = self.clean_text(raw_text)
            
            # Chunk
            chunks = self.chunk_text(cleaned_text, chunk_size=1000, chunk_overlap=200)
            logger.info(f"Split document into {len(chunks)} chunks.")
            
            # Save chunks to Relational DB
            # Remove existing chunks if any (re-processing safety)
            db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()
            
            db_chunks = []
            for i, chunk_text in enumerate(chunks):
                db_chunk = DocumentChunk(
                    document_id=document_id,
                    chunk_text=chunk_text,
                    chunk_index=i
                )
                db_chunks.append(db_chunk)
                
            db.add_all(db_chunks)
            db.commit()
            
            # Embed and Save to Qdrant
            # Remove existing chunks in Qdrant first
            qdrant_store.delete_document_chunks(document_id)
            
            # Add to Qdrant
            success = qdrant_store.add_chunks(document_id, chunks)
            if not success:
                raise RuntimeError("Failed to add chunks to Qdrant vector store.")
                
            # Update status
            doc.status = "Processed"
            db.commit()
            return True, "Document processed successfully."
            
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}")
            doc.status = "Failed"
            db.commit()
            return False, str(e)

pdf_service = PDFService()
