import joblib
import numpy as np
import os
import pandas as pd

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE       = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE, 'air_quality_model.pkl')

# ── Load model ────────────────────────────────────────────────────────────────
if not os.path.exists(MODEL_PATH):
    print("Model not found! Run train_model.py first.")
    exit()

model = joblib.load(MODEL_PATH)
print("Model loaded successfully.\n")

LABELS = {0: "✅ Safe", 1: "⚠️ Moderate", 2: "🚨 Dangerous"}

# ── Predict function ──────────────────────────────────────────────────────────
def predict(temperature, humidity, gas_raw):
    features = pd.DataFrame([[temperature, humidity, gas_raw]], 
                         columns=['temperature', 'humidity', 'gas_raw'])
    prediction = model.predict(features)[0]
    probability = model.predict_proba(features)[0]
    
    print(f"Temperature : {temperature} °C")
    print(f"Humidity    : {humidity} %")
    print(f"Gas Raw     : {gas_raw}")
    print(f"Prediction  : {LABELS[prediction]}")
    print(f"Confidence  : {max(probability) * 100:.1f}%")
    print("-" * 35)
    
    return prediction

# ── Test predictions ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Running test predictions...\n")
    
    predict(28.5, 65.0, 420)   # Expected: Safe
    predict(30.5, 62.0, 850)   # Expected: Moderate
    predict(33.0, 58.0, 1800)  # Expected: Dangerous