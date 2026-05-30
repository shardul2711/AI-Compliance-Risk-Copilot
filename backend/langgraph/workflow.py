from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, START, END
import json
import logging
from datetime import datetime

from backend.app.db.session import SessionLocal
from backend.app.models.models import (
    Document, Clause, ComplianceResult, RiskAssessment,
    Recommendation, ExecutiveReport, AuditLog
)
from backend.agents.document_agent import run_document_classification_agent
from backend.agents.clause_agent import run_clause_extraction_agent
from backend.agents.compliance_agent import run_compliance_mapping_agent
from backend.agents.risk_agent import run_risk_analysis_agent
from backend.agents.prediction_agent import run_ml_prediction_agent
from backend.agents.recommendation_agent import run_recommendation_agent
from backend.agents.report_agent import run_executive_report_agent

logger = logging.getLogger(__name__)

# Define state object structure
class AgentState(TypedDict):
    document_id: int
    filename: str
    document_text: str
    document_type: str
    extracted_clauses: List[Dict[str, Any]]
    compliance_results: List[Dict[str, Any]]
    risks: List[Dict[str, Any]]
    risk_score: float
    risk_level: str
    prediction_model: str
    explanation: List[str]
    recommendations: List[str]
    executive_summary: str

def write_audit_log(document_id: int, agent_name: str, action: str, input_data: Any, output_data: Any):
    """Utility to write execution logs to audit table."""
    db = SessionLocal()
    try:
        log = AuditLog(
            document_id=document_id,
            agent_name=agent_name,
            action=action,
            input_data=json.dumps(input_data, default=str),
            output_data=json.dumps(output_data, default=str)
        )
        db.add(log)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to write audit log for {agent_name}: {e}")
    finally:
        db.close()

# Define Agent Node Functions
async def classification_node(state: AgentState) -> Dict[str, Any]:
    logger.info("LangGraph - Classification Node starting...")
    res = await run_document_classification_agent(state["document_text"])
    
    write_audit_log(
        document_id=state["document_id"],
        agent_name="Document Classification Agent",
        action="Classify document type",
        input_data={"snippet": state["document_text"][:2000]},
        output_data=res
    )
    return {"document_type": res["document_type"]}

async def clause_extraction_node(state: AgentState) -> Dict[str, Any]:
    logger.info("LangGraph - Clause Extraction Node starting...")
    res = await run_clause_extraction_agent(state["document_text"])
    
    write_audit_log(
        document_id=state["document_id"],
        agent_name="Clause Extraction Agent",
        action="Extract clauses & risk levels",
        input_data={"snippet": state["document_text"][:2000]},
        output_data=res
    )
    return {"extracted_clauses": res["clauses"]}

async def compliance_mapping_node(state: AgentState) -> Dict[str, Any]:
    logger.info("LangGraph - Compliance Mapping Node starting...")
    res = await run_compliance_mapping_agent(state["document_text"], state["extracted_clauses"])
    
    write_audit_log(
        document_id=state["document_id"],
        agent_name="Compliance Mapping Agent",
        action="Check regulatory mapping",
        input_data={"clauses_count": len(state["extracted_clauses"])},
        output_data=res
    )
    return {"compliance_results": res["compliance_gaps"]}

async def risk_analysis_node(state: AgentState) -> Dict[str, Any]:
    logger.info("LangGraph - Risk Analysis Node starting...")
    res = await run_risk_analysis_agent(state["document_text"], state["extracted_clauses"], state["compliance_results"])
    
    write_audit_log(
        document_id=state["document_id"],
        agent_name="Risk Analysis Agent",
        action="Identify business & GRC risks",
        input_data={
            "clauses_count": len(state["extracted_clauses"]),
            "gaps_count": len(state["compliance_results"])
        },
        output_data=res
    )
    return {"risks": res["risks"]}

async def ml_prediction_node(state: AgentState) -> Dict[str, Any]:
    logger.info("LangGraph - ML Prediction & SHAP Node starting...")
    res = await run_ml_prediction_agent(state["document_text"], state["extracted_clauses"])
    
    write_audit_log(
        document_id=state["document_id"],
        agent_name="ML Prediction Agent",
        action="Calculate risk score and SHAP explanation",
        input_data=res.get("features", {}),
        output_data={
            "risk_score": res["risk_score"],
            "risk_level": res["risk_level"],
            "explanation": res["explanation"]
        }
    )
    return {
        "risk_score": res["risk_score"],
        "risk_level": res["risk_level"],
        "prediction_model": res["prediction_model"],
        "explanation": res["explanation"]
    }

async def recommendation_node(state: AgentState) -> Dict[str, Any]:
    logger.info("LangGraph - Recommendation Node starting...")
    res = await run_recommendation_agent(
        state["document_type"],
        state["extracted_clauses"],
        state["compliance_results"],
        state["risks"]
    )
    
    write_audit_log(
        document_id=state["document_id"],
        agent_name="Recommendation Agent",
        action="Generate mitigations and corrective actions",
        input_data={
            "document_type": state["document_type"],
            "risks_count": len(state["risks"]),
            "gaps_count": len(state["compliance_results"])
        },
        output_data=res
    )
    return {"recommendations": res["recommendations"]}

async def report_node(state: AgentState) -> Dict[str, Any]:
    logger.info("LangGraph - Executive Report Node starting...")
    res = await run_executive_report_agent(
        filename=state["filename"],
        document_type=state["document_type"],
        risk_score=state["risk_score"],
        risk_level=state["risk_level"],
        extracted_clauses=state["extracted_clauses"],
        compliance_gaps=state["compliance_results"],
        risks=state["risks"],
        recommendations=state["recommendations"]
    )
    
    write_audit_log(
        document_id=state["document_id"],
        agent_name="Executive Report Agent",
        action="Compile final Markdown report",
        input_data={"risk_score": state["risk_score"], "risk_level": state["risk_level"]},
        output_data={"report_length": len(res["summary"])}
    )
    return {"executive_summary": res["summary"]}


# Build the Workflow Graph
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("classify", classification_node)
workflow.add_node("extract_clauses", clause_extraction_node)
workflow.add_node("map_compliance", compliance_mapping_node)
workflow.add_node("analyze_risks", risk_analysis_node)
workflow.add_node("ml_predict", ml_prediction_node)
workflow.add_node("recommend", recommendation_node)
workflow.add_node("generate_report", report_node)

# Set up edges
workflow.add_edge(START, "classify")
workflow.add_edge("classify", "extract_clauses")
workflow.add_edge("extract_clauses", "map_compliance")
workflow.add_edge("map_compliance", "analyze_risks")
workflow.add_edge("analyze_risks", "ml_predict")
workflow.add_edge("ml_predict", "recommend")
workflow.add_edge("recommend", "generate_report")
workflow.add_edge("generate_report", END)

# Compile Graph
compiled_workflow = workflow.compile()


async def run_compliance_copilot_workflow(document_id: int, filename: str, document_text: str) -> Dict[str, Any]:
    """
    Entrypoint to run the full multi-agent workflow on a document.
    Saves output states to the relational database upon completion.
    """
    initial_state = {
        "document_id": document_id,
        "filename": filename,
        "document_text": document_text,
        "document_type": "",
        "extracted_clauses": [],
        "compliance_results": [],
        "risks": [],
        "risk_score": 0.0,
        "risk_level": "Low",
        "prediction_model": "",
        "explanation": [],
        "recommendations": [],
        "executive_summary": ""
    }
    
    logger.info(f"Triggering LangGraph workflow for document {document_id} ({filename})...")
    final_state = await compiled_workflow.ainvoke(initial_state)
    
    # Save the analysis results to MySQL database
    db = SessionLocal()
    try:
        # Update Document record metadata
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.document_type = final_state["document_type"]
            doc.status = "Analyzed"
            
            # 1. Save Clauses
            db.query(Clause).filter(Clause.document_id == document_id).delete()
            for c in final_state["extracted_clauses"]:
                clause_record = Clause(
                    document_id=document_id,
                    clause_type=c["clause_type"],
                    clause_text=c["clause_text"],
                    risk_level=c["risk_level"]
                )
                db.add(clause_record)
                
            # 2. Save Compliance Mapping
            db.query(ComplianceResult).filter(ComplianceResult.document_id == document_id).delete()
            for cr in final_state["compliance_results"]:
                comp_record = ComplianceResult(
                    document_id=document_id,
                    framework=cr["framework"],
                    requirement=cr["requirement"],
                    status=cr["status"],
                    gap_description=cr["gap_description"]
                )
                db.add(comp_record)
                
            # 3. Save Risk Assessment
            db.query(RiskAssessment).filter(RiskAssessment.document_id == document_id).delete()
            risk_record = RiskAssessment(
                document_id=document_id,
                risk_score=final_state["risk_score"],
                risk_level=final_state["risk_level"],
                prediction_model=final_state["prediction_model"]
            )
            db.add(risk_record)
            
            # 4. Save Recommendations
            db.query(Recommendation).filter(Recommendation.document_id == document_id).delete()
            for rec in final_state["recommendations"]:
                rec_record = Recommendation(
                    document_id=document_id,
                    recommendation=rec
                )
                db.add(rec_record)
                
            # 5. Save Executive Report
            db.query(ExecutiveReport).filter(ExecutiveReport.document_id == document_id).delete()
            report_record = ExecutiveReport(
                document_id=document_id,
                summary=final_state["executive_summary"]
            )
            db.add(report_record)
            
            # Add SHAP explanations as audit logs or recommendations if needed.
            # We already have detailed audit logs.
            db.commit()
            logger.info(f"Successfully saved LangGraph workflow results for document {document_id}.")
            
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving workflow results to database: {e}")
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.status = "Failed"
            db.commit()
    finally:
        db.close()
        
    return final_state
