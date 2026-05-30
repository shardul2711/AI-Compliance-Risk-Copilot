import pandas as pd
import numpy as np
import os

def generate_synthetic_data(output_path: str, num_rows: int = 10000):
    np.random.seed(42)
    
    # Generate features
    privacy_clause = np.random.binomial(1, 0.75, num_rows)     # 75% have privacy clauses
    security_clause = np.random.binomial(1, 0.80, num_rows)    # 80% have security clauses
    termination_clause = np.random.binomial(1, 0.70, num_rows) # 70% have termination clauses
    liability_clause = np.random.binomial(1, 0.85, num_rows)   # 85% have liability clauses
    
    country_risk = np.random.uniform(0.0, 1.0, num_rows)
    penalty_amount = np.random.uniform(0.0, 1000000.0, num_rows)
    document_length = np.random.randint(500, 20000, num_rows)
    
    # Calculate continuous risk score (0-100)
    # Base risk is 25. Missing clauses add risk. High country risk and high penalties add risk.
    base_risk = 20.0
    
    risk_score = (
        base_risk +
        (1 - privacy_clause) * 15.0 +
        (1 - security_clause) * 15.0 +
        (1 - termination_clause) * 10.0 +
        (1 - liability_clause) * 12.0 +
        country_risk * 25.0 +
        (penalty_amount / 1000000.0) * 15.0 +
        (document_length / 20000.0) * 5.0 +
        np.random.normal(0, 4.0, num_rows) # add some noise
    )
    
    # Clip risk score to be between 0 and 100
    risk_score = np.clip(risk_score, 0.0, 100.0)
    
    # Determine risk level based on specifications:
    # 0-25 Low, 26-50 Medium, 51-75 High, 76-100 Critical
    risk_level = []
    for score in risk_score:
        if score <= 25.0:
            risk_level.append("Low")
        elif score <= 50.0:
            risk_level.append("Medium")
        elif score <= 75.0:
            risk_level.append("High")
        else:
            risk_level.append("Critical")
            
    df = pd.DataFrame({
        "privacy_clause": privacy_clause,
        "security_clause": security_clause,
        "termination_clause": termination_clause,
        "liability_clause": liability_clause,
        "country_risk": country_risk,
        "penalty_amount": penalty_amount,
        "document_length": document_length,
        "risk_score": risk_score,
        "risk_level": risk_level
    })
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Generated synthetic dataset with {num_rows} rows at: {output_path}")
    print(df.head())

if __name__ == "__main__":
    output_dir = os.path.dirname(os.path.abspath(__file__))
    generate_synthetic_data(os.path.join(output_dir, "synthetic_risk_data.csv"))
