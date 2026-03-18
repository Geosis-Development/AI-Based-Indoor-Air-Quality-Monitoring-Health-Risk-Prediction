import pandas as pd
import numpy as np
import joblib
import os
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE       = os.path.dirname(os.path.abspath(__file__))
DATA_PATH  = os.path.join(BASE, '..', 'dataset', 'processed', 'labeled_data.csv')
MODEL_PATH = os.path.join(BASE, 'air_quality_model.pkl')

# ── Load data ─────────────────────────────────────────────────────────────────
print("Loading dataset...")
df = pd.read_csv(DATA_PATH)
print(f"Dataset shape: {df.shape}")
print(df.head())

# ── Label if not already labeled ─────────────────────────────────────────────
if 'label' not in df.columns:
    def assign_label(row):
        if row['gas_raw'] < 600 and row['temperature'] < 30 and row['humidity'] < 70:
            return 0  # Safe
        elif row['gas_raw'] < 1200:
            return 1  # Moderate
        else:
            return 2  # Dangerous
    df['label'] = df.apply(assign_label, axis=1)
    df.to_csv(DATA_PATH, index=False)
    print("Labels assigned and saved.")

# ── Features & target ─────────────────────────────────────────────────────────
FEATURES = ['temperature', 'humidity', 'gas_raw']
X = df[FEATURES]
y = df['label']

print(f"\nClass distribution:\n{y.value_counts()}")

# ── Train / test split ────────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# ── Train model ───────────────────────────────────────────────────────────────
print("\nTraining Random Forest model...")
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# ── Evaluate ──────────────────────────────────────────────────────────────────
y_pred = model.predict(X_test)
print("\nClassification Report:")
print(classification_report(y_test, y_pred,
      target_names=['Safe', 'Moderate', 'Dangerous']))

# ── Confusion matrix ──────────────────────────────────────────────────────────
cm = confusion_matrix(y_test, y_pred)
plt.figure(figsize=(6, 4))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=['Safe', 'Moderate', 'Dangerous'],
            yticklabels=['Safe', 'Moderate', 'Dangerous'])
plt.title('Confusion Matrix')
plt.ylabel('Actual')
plt.xlabel('Predicted')
plt.tight_layout()
plt.savefig(os.path.join(BASE, 'confusion_matrix.png'))
print("Confusion matrix saved.")

# ── Feature importance ────────────────────────────────────────────────────────
importances = model.feature_importances_
plt.figure(figsize=(6, 3))
sns.barplot(x=importances, y=FEATURES, palette='viridis')
plt.title('Feature Importance')
plt.tight_layout()
plt.savefig(os.path.join(BASE, 'feature_importance.png'))
print("Feature importance chart saved.")

# ── Save model ────────────────────────────────────────────────────────────────
joblib.dump(model, MODEL_PATH)
print(f"\nModel saved to {MODEL_PATH}")