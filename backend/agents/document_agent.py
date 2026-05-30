import json
import logging
from backend.agents.llm_client import call_ollama

logger = logging.getLogger(__name__)

async def run_document_classification_agent(document_text: str) -> dict:
    """
    Classifies the document into one of: Contract, NDA, Policy, Regulation, Vendor Agreement.
    """
    logger.info("Running Document Classification Agent...")
    
    # We pass the first 4000 characters to classify, as headers usually contain classification information
    snippet = document_text[:4000]
    
    system_prompt = (
        "You are an expert document classification agent. Your task is to analyze the document text and "
        "classify it into exactly one of these types: 'Contract', 'NDA', 'Policy', 'Regulation', 'Vendor Agreement'. "
        "You must return the result as a JSON object with a single key 'document_type'."
    )
    
    prompt = f"""Analyze this document text snippet and classify it:
---
{snippet}
---

Return ONLY a JSON object:
{{
  "document_type": "<Contract | NDA | Policy | Regulation | Vendor Agreement>"
}}"""

    response_text = await call_ollama(prompt, system_prompt=system_prompt, json_mode=True)
    
    try:
        data = json.loads(response_text)
        doc_type = data.get("document_type", "Contract")
        
        # Validate that the type is one of the supported types
        valid_types = ["Contract", "NDA", "Policy", "Regulation", "Vendor Agreement"]
        if doc_type not in valid_types:
            # Simple fuzzy matching
            matched = False
            for vt in valid_types:
                if vt.lower() in doc_type.lower():
                    doc_type = vt
                    matched = True
                    break
            if not matched:
                doc_type = "Contract" # default fallback
                
        return {"document_type": doc_type}
    except Exception as e:
        logger.error(f"Failed to parse document classification response: {e}. Raw text: {response_text}")
        return {"document_type": "Contract"}  # Default fallback
