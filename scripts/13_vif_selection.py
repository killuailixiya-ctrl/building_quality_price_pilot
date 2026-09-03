from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from statsmodels.stats.outliers_influence import variance_inflation_factor
import statsmodels.api as sm

ROOT = Path(r"D:\Codex\building_01")
df = pd.read_csv(ROOT / "data/processed/feature_matrix.csv")
exclude = {"block_id", "city", "year", "centroid_x", "centroid_y"}
features = [c for c in df.columns if c not in exclude and c != "block_price"]
X = df[features].copy().fillna(df[features].median())

kept = features[:]
while True:
    Xk = sm.add_constant(X[kept])
    vif = pd.Series(
        [variance_inflation_factor(Xk.values, i) for i in range(1, Xk.shape[1])],
        index=Xk.columns[1:],
    )
    maxv = vif.max()
    if maxv <= 10:
        break
    drop = vif.idxmax()
    kept.remove(drop)

out = {
    "kept_features": kept,
    "dropped_count": len(features) - len(kept),
    "final_vif": vif.to_dict(),
}
(ROOT / "reports/vif_selection.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
final = df[["block_id", "block_price", "centroid_x", "centroid_y"] + kept].copy()
final.to_csv(ROOT / "data/processed/feature_matrix_vif.csv", index=False, encoding="utf-8-sig")
print(json.dumps(out, ensure_ascii=False, indent=2))
