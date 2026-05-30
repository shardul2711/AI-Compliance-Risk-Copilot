import json
import logging
from typing import List
from backend.agents.llm_client import call_ollama
from backend.app.services.ml_service import ml_service

logger = logging.getLogger(__name__)

async def run_ml_prediction_agent(document_text: str, extracted_clauses: List[dict]) -> dict:
    """
    Extracts numerical and categorical features for the ML model, runs prediction,
    and retrieves SHAP-based explainability.
    
    ML Features needed:
    - privacy_clause (0 or 1)
    - security_clause (0 or 1)
    - termination_clause (0 or 1)
    - liability_clause (0 or 1)
    - country_risk (0.0 to 1.0)
    - penalty_amount (float)
    - document_length (int)
    """
    logger.info("Running ML Prediction & Explainability Agents...")
    
    # 1. Determine presence of core clauses
    clause_types = [c.get("clause_type") for c in extracted_clauses]
    
    privacy_clause = 1 if "Data Privacy" in clause_types else 0
    security_clause = 1 if "Security" in clause_types else 0
    termination_clause = 1 if "Termination" in clause_types else 0
    liability_clause = 1 if "Liability" in clause_types else 0
    
    # 2. Extract penalty amount and country risk using LLM
    snippet = document_text[:12000]
    
    system_prompt = (
        "You are an expert financial and risk analyst. Your job is to read the document snippet "
        "and extract two values:\n"
        "1. The penalty amount or financial liability cap explicitly mentioned (in USD). If multiple are mentioned, return the highest. If none are mentioned, return 0.\n"
        "2. The country risk index (a decimal between 0.0 and 1.0) of the governing jurisdiction or countries involved. E.g. US/UK/EU governing laws = 0.1 to 0.3. High-risk developing nations or tax havens = 0.6 to 0.9. Default to 0.25 if not specified.\n"
        "Return the output as a JSON object with keys 'penalty_amount' and 'country_risk'."
    )
    
    prompt = f"""Read the document text and extract the penalty amount and country risk index:
---
{snippet}
---

Your response MUST be a JSON object:
{{
  "penalty_amount": <float, e.g. 50000.0 or 0>,
  "country_risk": <float between 0.0 and 1.0, e.g. 0.2>
}}"""

    response_text = await call_ollama(prompt, system_prompt=system_prompt, json_mode=True)
    
    penalty_amount = 0.0
    country_risk = 0.25
    
    try:
        data = json.loads(response_text)
        penalty_amount = float(data.get("penalty_amount", 0.0))
        country_risk = float(data.get("country_risk", 0.25))
        # Ensure country risk is within boundaries
        country_risk = max(0.0, min(1.0, country_risk))
    except Exception as e:
        logger.error(f"Failed to parse ML features: {e}. Raw response: {response_text}")
        
    document_length = len(document_text)
    
    logger.info(
        f"Features extracted: Privacy={privacy_clause}, Security={security_clause}, "
        f"Termination={termination_clause}, Liability={liability_clause}, "
        f"CountryRisk={country_risk}, Penalty={penalty_amount}, Len={document_length}"
    )
    
    # 3. Call ML Service
    try:
        prediction_results = ml_service.predict_risk(
            privacy_clause=privacy_clause,
            security_clause=security_clause,
            termination_clause=termination_clause,
            liability_clause=liability_clause,
            country_risk=country_risk,
            penalty_amount=penalty_amount,
            document_length=document_length
        )
        return {
            "risk_score": prediction_results["risk_score"],
            "risk_level": prediction_results["risk_level"],
            "prediction_model": prediction_results["model_used"],
            "explanation": prediction_results["explanation"],
            # Return features for audit logging convenience
            "features": {
                "privacy_clause": privacy_clause,
                "security_clause": security_clause,
                "termination_clause": termination_clause,
                "liability_clause": liability_clause,
                "country_risk": country_risk,
                "penalty_amount": penalty_amount,
                "document_length": document_length
            }
        }
    except Exception as e:
        logger.error(f"Error executing ML Prediction: {e}")
        # Fallback if ML service fails
        return {
            "risk_score": 50.0,
            "risk_level": "Medium",
            "prediction_model": "Fallback",
            "explanation": ["ML prediction service failed, returned fallback risk profile."],
            "features": {}
        }
