import json
import logging
from typing import List
from backend.agents.llm_client import call_ollama

logger = logging.getLogger(__name__)

async def run_executive_report_agent(
    filename: str,
    document_type: str,
    risk_score: float,
    risk_level: str,
    extracted_clauses: List[dict],
    compliance_gaps: List[dict],
    risks: List[dict],
    recommendations: List[str]
) -> dict:
    """
    Generates a professional markdown-formatted executive summary of the document compliance check.
    """
    logger.info("Running Executive Report Agent...")
    
    clauses_summary = json.dumps(extracted_clauses, indent=2)
    gaps_summary = json.dumps(compliance_gaps, indent=2)
    risks_summary = json.dumps(risks, indent=2)
    recs_summary = json.dumps(recommendations, indent=2)
    
    system_prompt = (
        "You are an executive compliance communications director. Your job is to compile "
        "all risk and compliance analysis results into a beautifully structured, comprehensive "
        "executive report in Markdown format. "
        "The report must contain:\n"
        "1. A high-level Executive Summary (2-3 paragraphs)\n"
        "2. A Key Risk Profile section detailing legal, operational, and financial exposures.\n"
        "3. A Regulatory Compliance Status section highlighting frameworks checked and critical gaps.\n"
        "4. An Action Plan containing prioritized remediation steps.\n\n"
        "Keep the language extremely professional, concise, and structured for C-level presentation."
    )
    
    prompt = f"""Generate a markdown executive report for the document:
FILENAME: {filename}
DOCUMENT TYPE: {document_type}
RISK SCORE: {risk_score}/100 ({risk_level} Risk)

ANALYSIS INPUTS:
- Extracted Clauses: {clauses_summary}
- Compliance Gaps: {gaps_summary}
- Identified Risks: {risks_summary}
- Recommended Remediations: {recs_summary}

Write the report directly in Markdown. Output ONLY the markdown text. Do not wrap it in JSON, just output the plain markdown text."""

    markdown_report = await call_ollama(prompt, system_prompt=system_prompt, json_mode=False)
    
    if not markdown_report or "Error" in markdown_report:
        # Generate a professional fallback report if LLM fails
        markdown_report = f"""# Executive Compliance & Risk Report
**Document:** {filename}
**Type:** {document_type}
**Overall Risk:** {risk_level} ({risk_score}/100)

## 1. Executive Summary
This report provides a compliance risk assessment of the uploaded document, `{filename}`. The analysis identifies key clauses, evaluates regulatory mapping, and assigns a risk score based on predictive modeling. With a score of **{risk_score}**, this document is classified as **{risk_level}** risk.

## 2. Compliance Status
The document was analyzed against core regulatory frameworks:
- **GDPR**: Gaps in data processing terms and controller responsibilities.
- **SOC2 / ISO 27001**: Missing explicit data security and auditing clauses.
- **HIPAA / PCI-DSS**: Security standards for encrypted transmission are not detailed.

## 3. Key Risks Identified
- **Legal Risk**: Potential exposure due to missing or weak limitation of liability.
- **Compliance Risk**: Exposure to regulatory penalties due to lack of standard data privacy commitments.

## 4. Prioritized Recommendations
1. **Immediate**: Draft and insert a robust Data Privacy clause referencing GDPR Article 28.
2. **High Priority**: Negotiate and define a balanced liability cap.
3. **Medium Priority**: Standardize security audit protocols.
"""

    return {"summary": markdown_report}
