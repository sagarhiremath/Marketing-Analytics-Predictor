# backend.py
import pandas as pd
import numpy as np
import io
import joblib
from pathlib import Path

# Path to your saved pipeline (must be in same folder or adjust path)
PIPELINE_PATH = Path(__file__).parent / "roi_pipeline.joblib"

# ---------- Load pipeline (safe) ----------
try:
    pipeline = joblib.load(PIPELINE_PATH)
except FileNotFoundError:
    raise FileNotFoundError(f"Can't find roi_pipeline.joblib at {PIPELINE_PATH}. Place your pipeline file there.")
except ModuleNotFoundError as e:
    # typical when a required package (e.g. xgboost) isn't installed
    raise ModuleNotFoundError(
        f"Module not found while loading pipeline: {e}. "
        "Install the missing package (for example: pip install xgboost) and try again."
    )
except Exception as e:
    raise RuntimeError(f"Error loading pipeline from {PIPELINE_PATH}: {e}")

# Try to obtain model and model_columns from pipeline structure
if isinstance(pipeline, dict):
    model = pipeline.get("model", None)
    scaler = pipeline.get("scaler", None)
    model_columns = pipeline.get("model_columns", [])
else:
    # If pipeline is a scikit-learn Pipeline or model object, use sensible defaults
    model = pipeline
    scaler = None
    model_columns = getattr(pipeline, "model_columns", [])

if model is None:
    raise RuntimeError("Loaded pipeline does not contain a 'model' entry and pipeline itself is not a model.")

# ---------- Prediction function ----------
def predict_campaign_revenue(user_input: dict) -> float:
    """
    Accepts user_input dict (same keys as used in app),
    returns predicted revenue (inverse-transformed if model predicted log1p).
    """
    one_hot_cols = ["Channel", "Objective", "Audience", "Geo", "Creative_Type"]
    binary_cols = ["Status"]

    # Step 1: DataFrame from input
    input_df = pd.DataFrame([user_input])

    # Step 2: Binary mapping
    for col in binary_cols:
        if col in input_df.columns:
            input_df[col] = input_df[col].map({"Completed": 1, "Active": 0})
        else:
            input_df[col] = 0

    # Step 3: Derived features
    impressions = int(input_df.get("Impressions_Till_Date", 0).values[0])
    clicks = int(input_df.get("Clicks_Till_Date", 0).values[0])
    conversions = int(input_df.get("Conversions_Till_Date", 0).values[0])
    spend = float(input_df.get("Spend_Till_Date", 0).values[0])

    input_df["CTR"] = (clicks / impressions) if impressions > 0 else 0.0
    input_df["CPC"] = (spend / clicks) if clicks > 0 else 0.0
    input_df["CPA"] = (spend / conversions) if conversions > 0 else 0.0

    # Step 4: Log transforms (match training transforms)
    input_df["Spend_Till_Date_log"] = np.log1p(spend)
    input_df["CPC_log"] = np.log1p(input_df["CPC"])
    input_df["CPA_log"] = np.log1p(input_df["CPA"])

    # Step 5: Drop raw columns if your training removed them
    drop_cols = ["Spend_Till_Date", "CPC", "CPA"]
    input_df = input_df.drop(columns=[c for c in drop_cols if c in input_df.columns])

    # Step 6: One-hot encode categorical columns (same approach as training)
    input_encoded = pd.get_dummies(input_df, columns=one_hot_cols, drop_first=True, dtype="int")

    # Step 7: Align columns with model's expected columns
    # If model_columns is empty, try to use input_encoded columns directly
    if model_columns:
        input_encoded = input_encoded.reindex(columns=model_columns, fill_value=0)

    # Step 8: Predict (ensure shape is correct)
    # Many models expect 2D array; scikit-like predict will accept a DataFrame
    prediction = model.predict(input_encoded)
    # If model predicted log1p(revenue), invert with expm1
    try:
        revenue = float(np.expm1(prediction[0]))
    except Exception:
        # fallback: if model predicted raw revenue
        revenue = float(prediction[0])

    return revenue

# ---------- to_excel (for download) ----------
def to_excel(df: pd.DataFrame) -> bytes:
    """Convert DataFrame to excel bytes for Streamlit download_button"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Results")
    return output.getvalue()
