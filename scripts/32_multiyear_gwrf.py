from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from pyproj import Transformer
import PyGRF

ROOT = Path(r"D:\Codex\building_01")
df = pd.read_csv(ROOT / "data/processed/multiyear_final_core.csv")
transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
cx, cy = transformer.transform(114.305, 30.593)
df["center_dist"] = np.sqrt((df["centroid_x"] - cx)**2 + (df["centroid_y"] - cy)**2)
df = df.dropna(subset=["block_price", "building_score_mean", "center_dist"])

poi_cols = [c for c in df.columns if c.endswith("_count") or c.endswith("_dist")]
base_features = ["building_score_mean", "center_dist", "metro_dist_current"] + poi_cols
df = pd.get_dummies(df, columns=["year", "district"], prefix=["year", "district"], drop_first=True)
features = base_features + [c for c in df.columns if c.startswith("year_") or c.startswith("district_")]
features = [c for c in features if c in df.columns]
features = list(dict.fromkeys(features))

X = df[features].copy().fillna(df[features].median())
y = np.log(df["block_price"])
coords = df[["centroid_x", "centroid_y"]].to_numpy(dtype=float)

Xtr, Xte, ytr, yte, ctr, cte = train_test_split(X, y, coords, test_size=0.2, random_state=42)

# RF baseline
rf = RandomForestRegressor(n_estimators=300, random_state=42, n_jobs=-1).fit(Xtr, ytr)
pr = rf.predict(Xte)
print("RF", r2_score(yte, pr), np.sqrt(mean_squared_error(yte, pr)), mean_absolute_error(yte, pr))

# GWRF
bw = min(100, len(Xtr)-1)
grf = PyGRF.PyGRFBuilder(band_width=bw, n_estimators=30, max_features=0.3, n_jobs=-1, train_weighted=False, predict_weighted=False, resampled=False, random_state=42)
grf.fit(Xtr, ytr, pd.DataFrame(ctr, columns=["x","y"]))
preds = grf.predict(Xte, pd.DataFrame(cte, columns=["x","y"]), local_weight=0.5)
pg = np.array(preds[0])
print("GWRF", r2_score(yte, pg), np.sqrt(mean_squared_error(yte, pg)), mean_absolute_error(yte, pg))

pd.DataFrame({
    "model": ["RF", "GWRF"],
    "r2": [r2_score(yte, pr), r2_score(yte, pg)],
    "rmse": [np.sqrt(mean_squared_error(yte, pr)), np.sqrt(mean_squared_error(yte, pg))],
    "mae": [mean_absolute_error(yte, pr), mean_absolute_error(yte, pg)],
}).to_csv(ROOT / "reports/multiyear_gwrf_metrics.csv", index=False, encoding="utf-8-sig")
