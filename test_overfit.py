import pandas as pd
import xgboost as xgb
from sklearn.model_selection import StratifiedKFold, cross_validate

df = pd.read_csv("sp500_data.csv")
df = df[df["analyst_rating"].isin(["Buy","Hold"])]

FEATURES = ["pe_ratio","div_yield_pct","beta","profit_margin","price_to_book",
            "debt_to_equity","roe_pct","earnings_growth","52w_position","revenue_bn"]

X = df[FEATURES].fillna(df[FEATURES].median())
y = (df["analyst_rating"] == "Buy").astype(int)

model = xgb.XGBClassifier(
    n_estimators=50, max_depth=2, learning_rate=0.05,
    min_child_weight=5, reg_alpha=0.1, reg_lambda=1.0,
    subsample=0.8, colsample_bytree=0.8,
    scale_pos_weight=3, random_state=42, verbosity=0
)

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
r = cross_validate(model, X, y, cv=cv,
                   scoring=["accuracy","roc_auc"],
                   return_train_score=True)

print(f"Train Acc : {r['train_accuracy'].mean():.3f}")
print(f"CV Acc    : {r['test_accuracy'].mean():.3f}")
print(f"CV ROC-AUC: {r['test_roc_auc'].mean():.3f}")
print(f"Gap       : {r['train_accuracy'].mean() - r['test_accuracy'].mean():.3f}")
