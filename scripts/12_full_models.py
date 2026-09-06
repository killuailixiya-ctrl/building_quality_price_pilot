from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split
import statsmodels.api as sm
from mgwr.gwr import GWR
import PyGRF

ROOT = Path(r"D:\Codex\building_01")
feature_csv = ROOT / "data/processed/feature_matrix.csv"
target = "block_price"
seed = 42

df = pd.read_csv(feature_csv)
exclude = {target, "block_id", "city", "year", "centroid_x", "centroid_y"}
features = [c for c in df.columns if c not in exclude]
X = df[features].copy()
X = X.fillna(X.median())
y = df[target].astype(float)
coords = df[["centroid_x", "centroid_y"]].to_numpy(dtype=float)

X_train, X_test, y_train, y_test, coords_train, coords_test = train_test_split(
    X, y, coords, test_size=0.2, random_state=seed
)

metrics = {}
# OLS
ols = sm.OLS(y_train, sm.add_constant(X_train)).fit()
ols_pred = ols.predict(sm.add_constant(X_test))
metrics["OLS"] = {
    "r2": r2_score(y_test, ols_pred),
    "rmse": np.sqrt(mean_squared_error(y_test, ols_pred)),
    "mae": mean_absolute_error(y_test, ols_pred),
}

# RandomForest
rf = RandomForestRegressor(n_estimators=300, random_state=seed, n_jobs=-1).fit(X_train, y_train)
rf_pred = rf.predict(X_test)
metrics["RF"] = {
    "r2": r2_score(y_test, rf_pred),
    "rmse": np.sqrt(mean_squared_error(y_test, rf_pred)),
    "mae": mean_absolute_error(y_test, rf_pred),
}

# GWR
try:
    gwr = GWR(coords_train, y_train.values, X_train.values, bw=100, kernel="gaussian", fixed=False).fit()
    gwr_pred = gwr.predict(coords_test, X_test.values)
    metrics["GWR"] = {
        "r2": r2_score(y_test, gwr_pred.predictions),
        "rmse": np.sqrt(mean_squared_error(y_test, gwr_pred.predictions)),
        "mae": mean_absolute_error(y_test, gwr_pred.predictions),
    }
except Exception as exc:
    metrics["GWR"] = {"error": str(exc)}

# GWRF
try:
    bw = min(100, len(X_train) - 1)
    grf = PyGRF.PyGRFBuilder(
        band_width=bw,
        n_estimators=50,
        max_features=0.3,
        n_jobs=-1,
        train_weighted=False,
        predict_weighted=False,
        resampled=False,
        random_state=seed,
    )
    grf.fit(X_train, y_train, pd.DataFrame(coords_train, columns=["x", "y"]))
    preds = grf.predict(X_test, pd.DataFrame(coords_test, columns=["x", "y"]), local_weight=0.5)
    grf_pred = np.array(preds[0])
    metrics["GWRF"] = {
        "r2": r2_score(y_test, grf_pred),
        "rmse": np.sqrt(mean_squared_error(y_test, grf_pred)),
        "mae": mean_absolute_error(y_test, grf_pred),
    }
except Exception as exc:
    metrics["GWRF"] = {"error": str(exc)}

out_json = ROOT / "reports/multimodel_metrics.json"
out_json.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
pd.DataFrame([{**v, "model": k} for k, v in metrics.items()]).to_csv(ROOT / "reports/multimodel_metrics.csv", index=False, encoding="utf-8-sig")
print(json.dumps(metrics, ensure_ascii=False, indent=2))

