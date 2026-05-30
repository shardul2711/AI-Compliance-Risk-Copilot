import json
import logging
from typing import List
from backend.agents.llm_client import call_ollama

logger = logging.getLogger(__name__)

async def run_risk_analysis_agent(document_text: str, extracted_clauses: List[dict], compliance_gaps: List[dict]) -> dict:
    """
    Identifies Legal, Financial, Operational, and Compliance risks in the document.
    """
    logger.info("Running Risk Analysis Agent...")
    
    snippet = document_text[:12000]
    clauses_summary = json.dumps(extracted_clauses, indent=2)
    gaps_summary = json.dumps(compliance_gaps, indent=2)
    
    system_prompt = (
        "You are an enterprise risk officer. Your job is to analyze the document text, "
        "extracted clauses, and identified compliance gaps to flag specific risks. "
        "Categorize risks into exactly these four areas:\n"
        "- Legal Risk: Exposure to litigation, breach of contract, or unenforceable clauses.\n"
        "- Financial Risk: Exposure to fines, excessive liability caps, payment delays, or cost overruns.\n"
        "- Operational Risk: Business interruption, data loss, vendor lock-in, or poor SLAs.\n"
        "- Compliance Risk: Gaps in regulatory alignment, missing audits, or lack of certification requirements.\n\n"
        "For each identified risk, write a clear description and assign a severity: 'Low', 'Medium', or 'High'. "
        "Return the output as a JSON object containing a 'risks' list."
    )
    
    prompt = f"""Identify risks in the document:

EXTRACTED CLAUSES:
{clauses_summary}

COMPLIANCE GAPS:
{gaps_summary}

DOCUMENT TEXT SNIPPET:
---
{snippet}
---

Your response MUST be a JSON object with this exact format:
{{
  "risks": [
    {{
      "risk_type": "Legal Risk | Financial Risk | Operational Risk | Compliance Risk",
      "description": "Clear description of the risk, why it exists, and the impact",
      "severity": "Low | Medium | High"
    }}
  ]
}}

Ensure you evaluate all four categories (at least one risk per category). Output only the JSON object."""

    response_text = await call_ollama(prompt, system_prompt=system_prompt, json_mode=True)
    
    try:
        data = json.loads(response_text)
        risks = data.get("risks", [])
        
        # Verify schema
        validated_risks = []
        valid_types = ["Legal Risk", "Financial Risk", "Operational Risk", "Compliance Risk"]
        valid_severities = ["Low", "Medium", "High"]
        
        for r in risks:
            rtype = r.get("risk_type")
            desc = r.get("description")
            sev = r.get("severity", "Low")
            
            if rtype and desc:
                matched_type = next((t for t in valid_types if t.lower() in rtype.lower()), None)
                if not matched_type:
                    continue
                    
                matched_sev = sev if sev in valid_severities else "Low"
                
                validated_risks.append({
                    "risk_type": matched_type,
                    "description": desc,
                    "severity": matched_sev
                })
                
        return {"risks": validated_risks}
    except Exception as e:
        logger.error(f"Failed to parse risk analysis response: {e}. Raw text: {response_text}")
        return {"risks": []}
