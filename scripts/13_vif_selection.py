from __future__ import annotations
import json
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from statsmodels.stats.outliers_influence import variance_inflation_factor
import statsmodels.api as sm

ROOT = Path(r"D:\Codex\building_01")
# 现在可通过命令行参数指定输入特征表和输出文件。
parser = argparse.ArgumentParser()
parser.add_argument("--input", default=str(ROOT / "data/processed/feature_matrix.csv"))
parser.add_argument("--output-csv", default=str(ROOT / "data/processed/feature_matrix_vif.csv"))
parser.add_argument("--output-json", default=str(ROOT / "reports/vif_selection.json"))
args = parser.parse_args()

df = pd.read_csv(args.input)
exclude = {"block_id", "city", "year", "centroid_x", "centroid_y"}
features = [c for c in df.columns if c not in exclude and c != "block_price"]
X = df[features].copy().fillna(df[features].median())
X = X.replace([np.inf, -np.inf], np.nan).fillna(X.median())
X = X[np.isfinite(X).all(axis=1)]

# 逐步剔除 VIF 最大的变量，直到所有 VIF <= 10。
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
Path(args.output_json).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
final = df[["block_id", "block_price", "centroid_x", "centroid_y"] + kept].copy()
final.to_csv(args.output_csv, index=False, encoding="utf-8-sig")
print(json.dumps(out, ensure_ascii=False, indent=2))

