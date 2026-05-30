import json
import logging
from backend.agents.llm_client import call_ollama

logger = logging.getLogger(__name__)

async def run_clause_extraction_agent(document_text: str) -> dict:
    """
    Extracts clauses (Confidentiality, Data Privacy, Liability, Termination, Security, Payment, Audit Rights)
    from the document text, along with their risk levels.
    """
    logger.info("Running Clause Extraction Agent...")
    
    # Analyze the first 16,000 characters of the document text
    snippet = document_text[:16000]
    
    system_prompt = (
        "You are a legal contract specialist agent. Your task is to analyze the document text "
        "and extract clauses belonging to these categories: 'Confidentiality', 'Data Privacy', "
        "'Liability', 'Termination', 'Security', 'Payment', 'Audit Rights'. "
        "For each found clause, extract the exact relevant text snippet and assign a risk level: "
        "'Low', 'Medium', or 'High'. "
        "Return the results as a JSON object with a single key 'clauses', which is a list of clause objects."
    )
    
    prompt = f"""Identify and extract clauses from this text:
---
{snippet}
---

Your response MUST be a JSON object with this exact format:
{{
  "clauses": [
    {{
      "clause_type": "Confidentiality | Data Privacy | Liability | Termination | Security | Payment | Audit Rights",
      "clause_text": "extracted exact text from the document",
      "risk_level": "Low | Medium | High"
    }}
  ]
}}

If a clause type is not mentioned or found, do not include it. Only output the JSON object."""

    response_text = await call_ollama(prompt, system_prompt=system_prompt, json_mode=True)
    
    try:
        data = json.loads(response_text)
        clauses = data.get("clauses", [])
        
        # Verify schema
        validated_clauses = []
        valid_types = ["Confidentiality", "Data Privacy", "Liability", "Termination", "Security", "Payment", "Audit Rights"]
        valid_risks = ["Low", "Medium", "High"]
        
        for c in clauses:
            ctype = c.get("clause_type")
            ctext = c.get("clause_text")
            crisk = c.get("risk_level", "Low")
            
            if ctype and ctext:
                # Normalize types and risks
                matched_type = next((vt for vt in valid_types if vt.lower() in ctype.lower()), None)
                if not matched_type:
                    continue  # ignore unrecognized types
                    
                matched_risk = crisk if crisk in valid_risks else "Low"
                
                validated_clauses.append({
                    "clause_type": matched_type,
                    "clause_text": ctext,
                    "risk_level": matched_risk
                })
                
        return {"clauses": validated_clauses}
    except Exception as e:
        logger.error(f"Failed to parse clause extraction response: {e}. Raw text: {response_text}")
        return {"clauses": []}
