from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split
import statsmodels.api as sm
import PyGRF
import arcpy
import geopandas as gpd

ROOT = Path(r"D:\Codex\building_01")
df = pd.read_csv(ROOT / "data/processed/feature_matrix_vif.csv")
exclude = {"block_id", "block_price", "centroid_x", "centroid_y"}
features = [c for c in df.columns if c not in exclude]
df = df.fillna(df.median(numeric_only=True))
df.to_csv(ROOT / "data/processed/model_input_filled.csv", index=False, encoding="utf-8-sig")

X = df[features].astype(float)
y = df["block_price"].astype(float)
coords = df[["centroid_x", "centroid_y"]].to_numpy(dtype=float)
X_train, X_test, y_train, y_test, coords_train, coords_test = train_test_split(
    X, y, coords, test_size=0.2, random_state=42
)

metrics = {}
ols = sm.OLS(y_train, sm.add_constant(X_train)).fit()
p = ols.predict(sm.add_constant(X_test))
metrics["OLS"] = {"r2": r2_score(y_test, p), "rmse": np.sqrt(mean_squared_error(y_test, p)), "mae": mean_absolute_error(y_test, p)}

rf = RandomForestRegressor(n_estimators=300, random_state=42, n_jobs=-1).fit(X_train, y_train)
p = rf.predict(X_test)
metrics["RF"] = {"r2": r2_score(y_test, p), "rmse": np.sqrt(mean_squared_error(y_test, p)), "mae": mean_absolute_error(y_test, p)}

try:
    grf = PyGRF.PyGRFBuilder(band_width=min(100, len(X_train)-1), n_estimators=50, max_features=0.3, n_jobs=-1, train_weighted=False, predict_weighted=False, resampled=False, random_state=42)
    grf.fit(X_train, y_train, pd.DataFrame(coords_train, columns=["x","y"]))
    preds = grf.predict(X_test, pd.DataFrame(coords_test, columns=["x","y"]), local_weight=0.5)
    p = np.array(preds[0])
    metrics["GWRF"] = {"r2": r2_score(y_test, p), "rmse": np.sqrt(mean_squared_error(y_test, p)), "mae": mean_absolute_error(y_test, p)}
except Exception as exc:
    metrics["GWRF"] = {"error": str(exc)}

try:
    arcpy.env.overwriteOutput = True
    points_gpkg = str(ROOT / "data/processed/model_points.gpkg")
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df["centroid_x"], df["centroid_y"]), crs="EPSG:3857")
    gdf.to_file(points_gpkg, layer="points", driver="GPKG")
    arcpy.management.MakeFeatureLayer(points_gpkg, "points_lyr")
    out = str(ROOT / "data/processed/gwr_out.gpkg")
    arcpy.stats.GWR(
        in_features="points_lyr",
        dependent_variable="block_price",
        model_type="CONTINUOUS",
        explanatory_variables=features,
        output_features=out,
        neighborhood_type="NUMBER_OF_NEIGHBORS",
        neighborhood_selection_method="USER_DEFINED",
        number_of_neighbors=100,
        local_weighting_scheme="GAUSSIAN",
    )
    rows = []
    fields = ["block_id", "block_price", "Predicted"]
    with arcpy.da.SearchCursor(out, fields) as cur:
        for row in cur:
            rows.append(row)
    g = pd.DataFrame(rows, columns=fields)
    metrics["GWR"] = {"r2": r2_score(g["block_price"], g["Predicted"]), "rmse": np.sqrt(mean_squared_error(g["block_price"], g["Predicted"])), "mae": mean_absolute_error(g["block_price"], g["Predicted"])}
except Exception as exc:
    metrics["GWR"] = {"error": str(exc)}

(ROOT / "reports/final_model_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(metrics, ensure_ascii=False, indent=2))
