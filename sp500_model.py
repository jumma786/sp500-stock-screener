"""
S&P 500 Analyst Rating Classifier
===================================
Binary classification: Buy vs Hold
Using XGBoost with cross-validation and SHAP analysis.

Usage:
  conda activate mlops
  pip install xgboost shap scikit-learn matplotlib --break-system-packages
  python sp500_model.py
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore")

from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb
import shap

# ── 1. Load data ──────────────────────────────────────────────────────────────
df = pd.read_csv("sp500_data.csv")
print(f"\nS&P 500 Analyst Rating Classifier")
print(f"{'='*45}")
print(f"Dataset: {df.shape[0]} stocks, {df.shape[1]} columns")

# Keep only Buy / Hold
df = df[df["analyst_rating"].isin(["Buy","Hold"])].copy()
print(f"After filter: {len(df)} stocks (Buy={sum(df['analyst_rating']=='Buy')}, Hold={sum(df['analyst_rating']=='Hold')})")

# ── 2. Features ───────────────────────────────────────────────────────────────
FEATURES = [
    "pe_ratio", "div_yield_pct", "beta", "profit_margin",
    "price_to_book", "debt_to_equity", "roe_pct",
    "earnings_growth", "52w_position", "revenue_bn"
]

X = df[FEATURES].copy()
y = (df["analyst_rating"] == "Buy").astype(int)  # 1=Buy, 0=Hold

# Impute missing with median
for col in FEATURES:
    X[col] = X[col].fillna(X[col].median())

print(f"\nFeatures: {FEATURES}")
print(f"Missing values after imputation: {X.isnull().sum().sum()}")
print(f"\nClass balance: Buy={y.sum()} ({y.mean():.1%}), Hold={len(y)-y.sum()} ({1-y.mean():.1%})")

# ── 3. Model ──────────────────────────────────────────────────────────────────
scale_pw = (y == 0).sum() / (y == 1).sum()  # handle imbalance

model = xgb.XGBClassifier(
    n_estimators=50,
    max_depth=2,
    learning_rate=0.05,
    min_child_weight=5,
    reg_alpha=0.1,
    reg_lambda=1.0,
    subsample=0.8,
    colsample_bytree=0.8,
    scale_pos_weight=scale_pw,
    eval_metric="logloss",
    random_state=42,
    verbosity=0
)

# ── 4. Cross-validation ───────────────────────────────────────────────────────
print(f"\n{'─'*45}")
print("Cross-validation (5-fold stratified)...")

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_results = cross_validate(
    model, X, y, cv=cv,
    scoring=["accuracy","roc_auc","f1"],
    return_train_score=True
)

print(f"\n  CV Accuracy : {cv_results['test_accuracy'].mean():.3f} ± {cv_results['test_accuracy'].std():.3f}")
print(f"  CV ROC-AUC  : {cv_results['test_roc_auc'].mean():.3f} ± {cv_results['test_roc_auc'].std():.3f}")
print(f"  CV F1       : {cv_results['test_f1'].mean():.3f} ± {cv_results['test_f1'].std():.3f}")
print(f"  Train Acc   : {cv_results['train_accuracy'].mean():.3f} (watch for overfitting)")

overfit_gap = cv_results['train_accuracy'].mean() - cv_results['test_accuracy'].mean()
if overfit_gap > 0.1:
    print(f"  WARNING: Overfitting gap = {overfit_gap:.3f} — model may be memorising training data")
else:
    print(f"  Overfitting gap = {overfit_gap:.3f} — acceptable")

# ── 5. Final fit on full data ─────────────────────────────────────────────────
model.fit(X, y)

y_pred = model.predict(X)
y_prob = model.predict_proba(X)[:, 1]

print(f"\n{'─'*45}")
print("Classification report (full dataset):")
print(classification_report(y, y_pred, target_names=["Hold","Buy"]))

print(f"ROC-AUC (full): {roc_auc_score(y, y_prob):.3f}")

# ── 6. Feature importance ─────────────────────────────────────────────────────
importance = pd.DataFrame({
    "feature": FEATURES,
    "importance": model.feature_importances_
}).sort_values("importance", ascending=False)

print(f"\n{'─'*45}")
print("Feature importance (XGBoost gain):")
print(importance.to_string(index=False))

fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.barh(importance["feature"][::-1], importance["importance"][::-1], color="#185FA5")
ax.set_xlabel("Importance score")
ax.set_title("Feature importance — S&P 500 analyst rating classifier")
ax.spines[["top","right"]].set_visible(False)
plt.tight_layout()
plt.savefig("feature_importance.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved: feature_importance.png")

# ── 7. SHAP analysis ──────────────────────────────────────────────────────────
print(f"\n{'─'*45}")
print("Running SHAP analysis...")

explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X)

plt.figure()
shap.summary_plot(shap_values, X, plot_type="bar", show=False)
plt.title("SHAP feature importance")
plt.tight_layout()
plt.savefig("shap_summary.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved: shap_summary.png")

# ── 8. Save predictions ───────────────────────────────────────────────────────
df_out = df.copy()
df_out["predicted_rating"] = np.where(y_pred == 1, "Buy", "Hold")
df_out["buy_probability"] = y_prob.round(3)
df_out["prediction_correct"] = (y_pred == y.values)
df_out.to_csv("sp500_predictions.csv", index=False)
print("Saved: sp500_predictions.csv")

# ── 9. Honest limitations ────────────────────────────────────────────────────
print(f"\n{'='*45}")
print("HONEST LIMITATIONS")
print(f"{'='*45}")
print("1. Point-in-time snapshot — no time series history")
print("2. Analyst ratings are opinions, not return outcomes")
print("3. 79% Buy base rate — high accuracy possible by predicting Buy always")
print("4. 504 stocks is small for a robust classifier")
print(f"5. Majority class baseline accuracy: {y.mean():.1%}")
print(f"   Model CV accuracy: {cv_results['test_accuracy'].mean():.1%}")
improvement = cv_results['test_accuracy'].mean() - y.mean()
print(f"   Improvement over baseline: {improvement:+.1%}")
print(f"\nDone. Open feature_importance.png and shap_summary.png to review.")
