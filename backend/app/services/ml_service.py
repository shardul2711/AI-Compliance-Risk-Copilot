import os
import pickle
import pandas as pd
import numpy as np
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class MLService:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.models_dir = os.path.join(self.base_dir, "ml", "models")
        self.model = None
        self.explainer = None
        self.feature_names = None
        self.metadata = None
        self._initialized = False

    def initialize(self):
        if self._initialized:
            return
            
        model_path = os.path.join(self.models_dir, "best_model.pkl")
        explainer_path = os.path.join(self.models_dir, "shap_explainer.pkl")
        features_path = os.path.join(self.models_dir, "feature_names.pkl")
        metadata_path = os.path.join(self.models_dir, "metadata.pkl")
        
        # Check if files exist; if not, run training
        if not (os.path.exists(model_path) and os.path.exists(explainer_path) and os.path.exists(features_path)):
            logger.info("ML Models not found. Training models first...")
            try:
                from backend.ml.training.generate_data import generate_synthetic_data
                from backend.ml.training.train import train_models
                
                data_path = os.path.join(self.base_dir, "ml", "training", "synthetic_risk_data.csv")
                generate_synthetic_data(data_path)
                train_models()
            except Exception as e:
                logger.error(f"Failed to auto-train models: {e}")
                raise RuntimeError(f"ML models could not be loaded or auto-trained: {e}")

        # Load assets
        try:
            with open(model_path, "rb") as f:
                self.model = pickle.load(f)
            with open(explainer_path, "rb") as f:
                self.explainer = pickle.load(f)
            with open(features_path, "rb") as f:
                self.feature_names = pickle.load(f)
            if os.path.exists(metadata_path):
                with open(metadata_path, "rb") as f:
                    self.metadata = pickle.load(f)
            self._initialized = True
            logger.info(f"ML Service initialized successfully. Loaded model: {self.metadata.get('model_name') if self.metadata else 'Unknown'}")
        except Exception as e:
            logger.error(f"Error loading ML model files: {e}")
            raise e

    def predict_risk(
        self,
        privacy_clause: int,
        security_clause: int,
        termination_clause: int,
        liability_clause: int,
        country_risk: float,
        penalty_amount: float,
        document_length: int
    ) -> Dict[str, Any]:
        """
        Runs ML model inference to predict risk score and maps it to a risk level.
        Returns:
            dict containing:
                - risk_score (float 0-100)
                - risk_level (str Low, Medium, High, Critical)
                - model_used (str)
                - explanation (list of strings explaining feature contributions using SHAP)
        """
        self.initialize()
        
        # Create input DataFrame
        input_data = pd.DataFrame([{
            "privacy_clause": int(privacy_clause),
            "security_clause": int(security_clause),
            "termination_clause": int(termination_clause),
            "liability_clause": int(liability_clause),
            "country_risk": float(country_risk),
            "penalty_amount": float(penalty_amount),
            "document_length": int(document_length)
        }], columns=self.feature_names)
        
        # Predict continuous score
        pred_score = self.model.predict(input_data)[0]
        # Clip to valid range just in case
        pred_score = float(np.clip(pred_score, 0.0, 100.0))
        
        # Map to risk level
        # 0-25 Low, 26-50 Medium, 51-75 High, 76-100 Critical
        if pred_score <= 25.0:
            level = "Low"
        elif pred_score <= 50.0:
            level = "Medium"
        elif pred_score <= 75.0:
            level = "High"
        else:
            level = "Critical"
            
        # Compute SHAP explanation
        explanations = []
        try:
            # shap_values is a list/array. For tree models it might return list of arrays or Explanation object
            shap_values = self.explainer(input_data)
            
            # Extract features importances
            # shap_values could be a 2D array or an Explanation object. We can check shape.
            if hasattr(shap_values, "values"):
                vals = shap_values.values[0]
                base_value = shap_values.base_values[0]
            else:
                # older shap version fallback
                vals = self.explainer.shap_values(input_data)[0]
                base_value = self.explainer.expected_value
                if isinstance(base_value, np.ndarray):
                    base_value = base_value[0]
            
            # Map contributions back to features
            contributions = []
            for col, val in zip(self.feature_names, vals):
                contributions.append((col, val))
                
            # Sort contributions by absolute value (most significant first)
            contributions.sort(key=lambda x: abs(x[1]), reverse=True)
            
            # Format into human-readable strings
            for col, val in contributions:
                direction = "increases" if val > 0 else "decreases"
                val_abs = abs(val)
                
                # Friendly names
                friendly_names = {
                    "privacy_clause": "Privacy Clause presence",
                    "security_clause": "Security Clause presence",
                    "termination_clause": "Termination Clause presence",
                    "liability_clause": "Liability Clause presence",
                    "country_risk": "Country Risk profile",
                    "penalty_amount": "Penalty Amount specification",
                    "document_length": "Document Length / Complexity"
                }
                name = friendly_names.get(col, col)
                
                # Provide detail about what the state is
                val_val = input_data.iloc[0][col]
                if col.endswith("_clause"):
                    state_str = "missing" if val_val == 0 else "present"
                elif col == "penalty_amount":
                    state_str = f"${val_val:,.2f}"
                elif col == "country_risk":
                    state_str = f"{val_val:.2f}"
                elif col == "document_length":
                    state_str = f"{val_val} chars"
                else:
                    state_str = str(val_val)
                    
                explanations.append(
                    f"{name} ({state_str}) {direction} risk score by {val_abs:.2f} points"
                )
        except Exception as e:
            logger.error(f"Error computing SHAP values: {e}")
            explanations = [
                "Feature contribution explanation unavailable due to explainer error.",
                f"Missing clauses and Country Risk profile are key factors."
            ]
            
        return {
            "risk_score": round(pred_score, 1),
            "risk_level": level,
            "model_used": self.metadata.get("model_name", "TreeRegressor") if self.metadata else "TreeRegressor",
            "prediction_model": self.metadata.get("model_name", "TreeRegressor") if self.metadata else "TreeRegressor",
            "explanation": explanations
        }

ml_service = MLService()
