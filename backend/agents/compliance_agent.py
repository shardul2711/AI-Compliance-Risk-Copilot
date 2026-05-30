import json
import logging
from typing import List
from backend.agents.llm_client import call_ollama

logger = logging.getLogger(__name__)

async def run_compliance_mapping_agent(document_text: str, extracted_clauses: List[dict]) -> dict:
    """
    Checks the document text and extracted clauses against compliance frameworks:
    GDPR, HIPAA, SOC2, ISO27001, PCI-DSS.
    """
    logger.info("Running Compliance Mapping Agent...")
    
    # We pass document snippet and extracted clauses as context
    snippet = document_text[:12000]
    clauses_summary = json.dumps(extracted_clauses, indent=2)
    
    system_prompt = (
        "You are an expert regulatory compliance auditor. Your job is to check the document "
        "and its clauses against the following compliance frameworks: GDPR, HIPAA, SOC2, ISO27001, PCI-DSS. "
        "Evaluate the key requirements for each framework. Specifically:\n"
        "- GDPR: User consent, data deletion rights, processor obligations, data protection officer.\n"
        "- HIPAA: PHI protection, security safeguards, business associate agreements.\n"
        "- SOC2: Log monitoring, access control, system backup policies.\n"
        "- ISO27001: Risk management, security policies, asset classifications.\n"
        "- PCI-DSS: Data masking, network security controls, transmission encryption.\n\n"
        "Assess whether the document satisfies these areas and return the status as "
        "'Compliant', 'Non-Compliant', or 'Partially-Compliant'. "
        "Provide a clear 'gap_description' if there is any deficiency. "
        "Return the output as a JSON object containing a 'compliance_gaps' list."
    )
    
    prompt = f"""Evaluate this document's compliance based on its text and extracted clauses:

EXTRACTED CLAUSES SUMMARY:
{clauses_summary}

DOCUMENT TEXT SNIPPET:
---
{snippet}
---

Your response MUST be a JSON object with this exact format:
{{
  "compliance_gaps": [
    {{
      "framework": "GDPR | HIPAA | SOC2 | ISO27001 | PCI-DSS",
      "requirement": "Short description of the requirement checked",
      "status": "Compliant | Non-Compliant | Partially-Compliant",
      "gap_description": "Description of what is missing or deficient, or null if Compliant"
    }}
  ]
}}

Provide assessments for all 5 frameworks (at least one check per framework). Output only the JSON object."""

    response_text = await call_ollama(prompt, system_prompt=system_prompt, json_mode=True)
    
    try:
        data = json.loads(response_text)
        gaps = data.get("compliance_gaps", [])
        
        # Verify schema
        validated_gaps = []
        valid_frameworks = ["GDPR", "HIPAA", "SOC2", "ISO27001", "PCI-DSS"]
        valid_statuses = ["Compliant", "Non-Compliant", "Partially-Compliant"]
        
        for g in gaps:
            fw = g.get("framework")
            req = g.get("requirement")
            status = g.get("status", "Non-Compliant")
            desc = g.get("gap_description")
            
            if fw and req:
                matched_fw = next((f for f in valid_frameworks if f.lower() in fw.lower()), None)
                if not matched_fw:
                    continue
                    
                matched_status = status if status in valid_statuses else "Non-Compliant"
                
                validated_gaps.append({
                    "framework": matched_fw,
                    "requirement": req,
                    "status": matched_status,
                    "gap_description": desc if matched_status != "Compliant" else None
                })
                
        return {"compliance_gaps": validated_gaps}
    except Exception as e:
        logger.error(f"Failed to parse compliance mapping response: {e}. Raw text: {response_text}")
        return {"compliance_gaps": []}
