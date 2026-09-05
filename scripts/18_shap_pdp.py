from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import shap
from sklearn.inspection import PartialDependenceDisplay
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(r"D:\Codex\building_01")
df = pd.read_csv(ROOT / "data/processed/feature_matrix_vif.csv")
df = df.dropna(subset=["block_price"]).copy()
exclude = {"block_id", "block_price", "centroid_x", "centroid_y"}
features = [c for c in df.columns if c not in exclude]
X = df[features].copy().fillna(df[features].median())
y = df["block_price"]

model = RandomForestRegressor(n_estimators=300, random_state=42, n_jobs=-1).fit(X, y)
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X)
imp = pd.Series(np.abs(shap_values).mean(0), index=features).sort_values(ascending=False)
imp.to_csv(ROOT / "reports/shap_importance.csv", index_label="feature")
imp.head(30).to_csv(ROOT / "reports/shap_importance_top30.csv")

top_features = imp.head(5).index.tolist()
fig, ax = plt.subplots(figsize=(10, 8))
PartialDependenceDisplay.from_estimator(model, X, top_features, ax=ax, grid_resolution=30)
fig.savefig(ROOT / "reports/pdp_top5.png", dpi=300, bbox_inches="tight")
plt.close(fig)

print(imp.head(15).to_string())
print("saved", ROOT / "reports/shap_importance.csv")
print("saved", ROOT / "reports/pdp_top5.png")
