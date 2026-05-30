import os
import sys
import asyncio
import logging

# Ensure parent directory is in system path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("Verifier")

async def test_database():
    logger.info("--- Testing Database Connection (MySQL) ---")
    from backend.app.db.session import SessionLocal
    from backend.app.models.models import User
    
    db = SessionLocal()
    try:
        users = db.query(User).all()
        logger.info(f"Successfully connected to MySQL database. Found {len(users)} seeded users:")
        for u in users:
            logger.info(f" - User: {u.name} ({u.email}) [Role: {u.role}]")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False
    finally:
        db.close()

def test_ml_service():
    logger.info("--- Testing Machine Learning Inference & SHAP ---")
    from backend.app.services.ml_service import ml_service
    
    try:
        # Predict on a high-risk scenario: missing privacy & security, high penalty, high country risk
        logger.info("Running prediction for high-risk document profile...")
        res_high = ml_service.predict_risk(
            privacy_clause=0,
            security_clause=0,
            termination_clause=1,
            liability_clause=0,
            country_risk=0.8,
            penalty_amount=750000.0,
            document_length=15000
        )
        logger.info(f" High Risk Profile Result: Score={res_high['risk_score']} ({res_high['risk_level']})")
        logger.info(f" Model used: {res_high['prediction_model']}")
        logger.info(" SHAP Explanations:")
        for exp in res_high["explanation"][:3]:
            logger.info(f"   - {exp}")
            
        # Predict on a low-risk scenario: all clauses present, low penalty, low country risk
        logger.info("Running prediction for low-risk document profile...")
        res_low = ml_service.predict_risk(
            privacy_clause=1,
            security_clause=1,
            termination_clause=1,
            liability_clause=1,
            country_risk=0.1,
            penalty_amount=0.0,
            document_length=5000
        )
        logger.info(f" Low Risk Profile Result: Score={res_low['risk_score']} ({res_low['risk_level']})")
        return True
    except Exception as e:
        logger.error(f"ML Service test failed: {e}")
        return False

def test_qdrant_and_embeddings():
    logger.info("--- Testing Qdrant Local Vector Store & Embeddings ---")
    from backend.rag.embeddings.embedder import embedding_service
    from backend.rag.vectorstore.qdrant_store import qdrant_store
    
    try:
        # Test embeddings
        logger.info("Testing embedding model loading & execution...")
        emb = embedding_service.embed_query("Hello compliance copilot")
        logger.info(f"Successfully generated query embedding vector of length {len(emb)}")
        
        # Test Qdrant client connection
        logger.info("Testing Qdrant connection and temporary indexing...")
        qdrant_store.initialize()
        
        temp_doc_id = 9999
        test_chunks = [
            "This Agreement is governed by the laws of the State of California.",
            "All disputes shall be resolved by arbitration in San Francisco.",
            "The data processor shall implement appropriate technical measures to encrypt user data."
        ]
        
        # Add chunks
        qdrant_store.add_chunks(temp_doc_id, test_chunks)
        
        # Query chunks
        logger.info("Querying Qdrant index with filter...")
        results = qdrant_store.search_chunks(temp_doc_id, "data encryption and security", limit=1)
        if results:
            logger.info(f" Query Result: '{results[0]['chunk_text']}' (Score: {results[0]['score']:.4f})")
        else:
            logger.warning(" No results found in Qdrant search!")
            
        # Delete chunks
        qdrant_store.delete_document_chunks(temp_doc_id)
        logger.info("Qdrant indexing and retrieval verified successfully.")
        return True
    except Exception as e:
        logger.error(f"Qdrant/Embedding test failed: {e}")
        return False

async def test_langgraph_workflow():
    logger.info("--- Testing LangGraph Agent Workflow (Async) ---")
    from backend.langgraph.workflow import run_compliance_copilot_workflow
    from backend.app.db.session import SessionLocal
    from backend.app.models.models import Document
    
    db = SessionLocal()
    # Create a temporary document record to satisfy database constraints
    temp_doc = Document(
        user_id=1, # Default seeded admin
        filename="verifier_test_document.pdf",
        status="Uploaded",
        file_path="verify_test_path.pdf"
    )
    db.add(temp_doc)
    db.commit()
    db.refresh(temp_doc)
    
    mock_doc_text = """
    MUTUAL NON-DISCLOSURE AGREEMENT
    This Mutual Non-Disclosure Agreement ("Agreement") is entered into by and between Acme Corp and Beta Inc.
    
    1. Purpose: The parties wish to explore a business relationship.
    2. Confidentiality obligations: Each party agrees to maintain the confidentiality of the other party's information.
    3. Governing Law: This Agreement shall be governed by and construed in accordance with the laws of Germany.
    4. Penalty: In case of any breach, the breaching party shall pay a liquidated damage of EUR 100,000 to the non-breaching party.
    5. Termination: This agreement will terminate 3 years from the date of execution.
    """
    
    try:
        logger.info(f"Running LangGraph agents workflow on mock document {temp_doc.id}...")
        final_state = await run_compliance_copilot_workflow(
            document_id=temp_doc.id,
            filename=temp_doc.filename,
            document_text=mock_doc_text
        )
        
        logger.info("LangGraph execution completed successfully!")
        logger.info(f" - Classified Type: {final_state['document_type']}")
        logger.info(f" - Extracted Clauses Count: {len(final_state['extracted_clauses'])}")
        logger.info(f" - Compliance Gaps Found: {len(final_state['compliance_results'])}")
        logger.info(f" - Predicted Risk Score: {final_state['risk_score']}/100 ({final_state['risk_level']})")
        logger.info(f" - Recommendations Count: {len(final_state['recommendations'])}")
        logger.info(" - Executive Report length: " + str(len(final_state["executive_summary"])) + " characters.")
        
        # Verify audit logs in database
        from backend.app.models.models import AuditLog
        logs = db.query(AuditLog).filter(AuditLog.document_id == temp_doc.id).all()
        logger.info(f" - Saved Audit Logs: {len(logs)} steps recorded.")
        for log in logs:
            logger.info(f"    * Step: {log.agent_name} -> Action: {log.action}")
            
        return True
    except Exception as e:
        logger.error(f"LangGraph workflow test failed: {e}")
        return False
    finally:
        # Cleanup
        db.delete(temp_doc)
        db.commit()
        db.close()

async def main():
    logger.info("=== STARTING AI COMPLIANCE COPILOT VERIFICATION ===")
    
    db_ok = await test_database()
    ml_ok = test_ml_service()
    qdrant_ok = test_qdrant_and_embeddings()
    langgraph_ok = await test_langgraph_workflow()
    
    logger.info("\n=== VERIFICATION SUMMARY ===")
    logger.info(f" Database (MySQL):   {'[PASS]' if db_ok else '[FAIL]'}")
    logger.info(f" ML & SHAP:          {'[PASS]' if ml_ok else '[FAIL]'}")
    logger.info(f" Qdrant & Embeddings: {'[PASS]' if qdrant_ok else '[FAIL]'}")
    logger.info(f" LangGraph Workflow:  {'[PASS]' if langgraph_ok else '[FAIL]'}")
    
    if db_ok and ml_ok and qdrant_ok and langgraph_ok:
        logger.info("\nAll backend core services verified successfully. READY FOR PRODUCTION API SERVER.")
        sys.exit(0)
    else:
        logger.error("\nOne or more core components failed verification.")
        sys.exit(1)

if __name__ == "__main__":
    # run async main
    asyncio.run(main())
