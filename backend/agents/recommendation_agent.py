import json
import logging
from typing import List
from backend.agents.llm_client import call_ollama

logger = logging.getLogger(__name__)

async def run_recommendation_agent(
    document_type: str,
    extracted_clauses: List[dict],
    compliance_gaps: List[dict],
    risks: List[dict]
) -> dict:
    """
    Generates actionable compliance suggestions and corrective actions based on gaps and risks.
    """
    logger.info("Running Recommendation Agent...")
    
    clauses_summary = json.dumps(extracted_clauses, indent=2)
    gaps_summary = json.dumps(compliance_gaps, indent=2)
    risks_summary = json.dumps(risks, indent=2)
    
    system_prompt = (
        "You are a GRC advisor. Your task is to generate actionable recommendations to mitigate the "
        "identified risks, address compliance gaps, and suggest draft clauses for any missing requirements. "
        "Make sure recommendations are clear, direct, and specify which framework (GDPR, HIPAA, etc.) "
        "or risk area they address. "
        "Return the output as a JSON object containing a 'recommendations' list of strings."
    )
    
    prompt = f"""Generate recommendations for this document:
DOCUMENT TYPE: {document_type}

EXTRACTED CLAUSES:
{clauses_summary}

COMPLIANCE GAPS:
{gaps_summary}

IDENTIFIED RISKS:
{risks_summary}

Your response MUST be a JSON object with this exact format:
{{
  "recommendations": [
    "Specific recommendation sentence 1...",
    "Specific recommendation sentence 2..."
  ]
}}

Provide at least 4 clear, specific recommendations. Output only the JSON object."""

    response_text = await call_ollama(prompt, system_prompt=system_prompt, json_mode=True)
    
    try:
        data = json.loads(response_text)
        recs = data.get("recommendations", [])
        
        # Simple schema filter
        validated_recs = [str(r) for r in recs if r]
        
        if not validated_recs:
            validated_recs = [
                "Insert standard Data Privacy clause complying with GDPR article 28 processor obligations.",
                "Amend the Liability section to include a reciprocal indemnification clause.",
                "Establish access control and log monitoring practices aligning with SOC2 criteria CC6.1.",
                "Conduct an information security risk assessment in accordance with ISO 27001 Annex A.12."
            ]
            
        return {"recommendations": validated_recs}
    except Exception as e:
        logger.error(f"Failed to parse recommendations: {e}. Raw response: {response_text}")
        return {"recommendations": [
            "Insert standard Data Privacy clause complying with GDPR article 28 processor obligations.",
            "Amend the Liability section to include a reciprocal indemnification clause."
        ]}
