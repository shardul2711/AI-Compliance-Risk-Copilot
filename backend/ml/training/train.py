import pandas as pd
import numpy as np
import pickle
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from sklearn.metrics import mean_squared_error, r2_score
from xgboost import XGBRegressor
import shap

def train_models():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, "training", "synthetic_risk_data.csv")
    models_dir = os.path.join(base_dir, "models")
    os.makedirs(models_dir, exist_ok=True)
    
    if not os.path.exists(data_path):
        print(f"Data path {data_path} not found. Please run generate_data.py first.")
        # Generate data automatically
        from backend.ml.training.generate_data import generate_synthetic_data
        generate_synthetic_data(data_path)
        
    df = pd.read_csv(data_path)
    
    # Features & Target
    # We do not use risk_level for training features since it's the target classification
    X = df.drop(columns=["risk_score", "risk_level"])
    y = df["risk_score"]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training models...")
    
    # 1. Random Forest Regressor
    rf = RandomForestRegressor(n_estimators=100, random_state=42)
    rf.fit(X_train, y_train)
    rf_preds = rf.predict(X_test)
    rf_mse = mean_squared_error(y_test, rf_preds)
    rf_r2 = r2_score(y_test, rf_preds)
    print(f"Random Forest - MSE: {rf_mse:.4f}, R2: {rf_r2:.4f}")
    
    # 2. XGBoost Regressor
    xgb = XGBRegressor(n_estimators=100, learning_rate=0.05, max_depth=5, random_state=42)
    xgb.fit(X_train, y_train)
    xgb_preds = xgb.predict(X_test)
    xgb_mse = mean_squared_error(y_test, xgb_preds)
    xgb_r2 = r2_score(y_test, xgb_preds)
    print(f"XGBoost - MSE: {xgb_mse:.4f}, R2: {xgb_r2:.4f}")
    
    # 3. SVM Regressor
    # SVR needs scaling, but since we are doing simple comparison and random forest/xgboost typically win on tabular datasets, we can train it directly or scale.
    # Let's run SVR directly or with standard parameters. SVR is sensitive, let's use it for comparison.
    svr = SVR(kernel="rbf")
    svr.fit(X_train, y_train)
    svr_preds = svr.predict(X_test)
    svr_mse = mean_squared_error(y_test, svr_preds)
    svr_r2 = r2_score(y_test, svr_preds)
    print(f"SVR - MSE: {svr_mse:.4f}, R2: {svr_r2:.4f}")
    
    # Determine best model
    models = {
        "RandomForest": (rf, rf_r2),
        "XGBoost": (xgb, xgb_r2),
        "SVR": (svr, svr_r2)
    }
    
    best_model_name = max(models, key=lambda k: models[k][1])
    best_model, best_r2 = models[best_model_name]
    print(f"\nBest Model: {best_model_name} with R2 score: {best_r2:.4f}")
    
    # Save best model
    model_save_path = os.path.join(models_dir, "best_model.pkl")
    with open(model_save_path, "wb") as f:
        pickle.dump(best_model, f)
    print(f"Saved best model to: {model_save_path}")
    
    # Create and save SHAP Explainer
    print("Generating SHAP Explainer...")
    
    # Tree explainer for RF/XGBoost is much faster and precise. SVR would need KernelExplainer.
    # We will instantiate TreeExplainer for Tree models, fallback to KernelExplainer if SVR wins.
    if best_model_name in ["RandomForest", "XGBoost"]:
        explainer = shap.TreeExplainer(best_model)
    else:
        # Sample training data to speed up KernelExplainer
        background_data = shap.kmeans(X_train, 10)
        explainer = shap.KernelExplainer(best_model.predict, background_data)
        
    explainer_save_path = os.path.join(models_dir, "shap_explainer.pkl")
    with open(explainer_save_path, "wb") as f:
        pickle.dump(explainer, f)
    print(f"Saved SHAP Explainer to: {explainer_save_path}")
    
    # Save the feature names for inference reference
    features_save_path = os.path.join(models_dir, "feature_names.pkl")
    with open(features_save_path, "wb") as f:
        pickle.dump(list(X.columns), f)
        
    # Also save metadata
    metadata = {
        "model_name": best_model_name,
        "r2": float(best_r2),
        "mse": float(rf_mse if best_model_name == "RandomForest" else (xgb_mse if best_model_name == "XGBoost" else svr_mse))
    }
    with open(os.path.join(models_dir, "metadata.pkl"), "wb") as f:
        pickle.dump(metadata, f)
    print("Training pipeline finished.")

if __name__ == "__main__":
    train_models()
