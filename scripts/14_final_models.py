from __future__ import annotations
import json
import argparse
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
parser = argparse.ArgumentParser()
parser.add_argument("--input", default=str(ROOT / "data/processed/feature_matrix_vif.csv"))
parser.add_argument("--output-json", default=str(ROOT / "reports/final_model_metrics.json"))
args = parser.parse_args()

df = pd.read_csv(args.input)
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
    gdb_path = str(ROOT / "data/processed/gwr_input.gdb")
    if not arcpy.Exists(gdb_path):
        arcpy.management.CreateFileGDB(str(ROOT / "data/processed"), "gwr_input.gdb")
    fc = gdb_path + "\\points"
    if arcpy.Exists(fc):
        arcpy.management.Delete(fc)
    sr = arcpy.SpatialReference(3857)
    arcpy.management.CreateFeatureclass(gdb_path, "points", "POINT", spatial_reference=sr)
    arcpy.management.AddField(fc, "block_id", "TEXT", field_length=32)
    arcpy.management.AddField(fc, "block_price", "DOUBLE")
    for feature in features:
        arcpy.management.AddField(fc, feature, "DOUBLE")
    cursor_fields = ["SHAPE@", "block_id", "block_price"] + features
    with arcpy.da.InsertCursor(fc, cursor_fields) as cur:
        for _, row in df.iterrows():
            point = arcpy.Point(float(row["centroid_x"]), float(row["centroid_y"]))
            values = [point, str(row["block_id"]), float(row["block_price"])]
            values += [float(row[feature]) for feature in features]
            cur.insertRow(values)
    out = gdb_path + "\\gwr_out"
    arcpy.stats.GWR(
        in_features=fc,
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
    fields = ["block_price", "PREDICTED"]
    with arcpy.da.SearchCursor(out, fields) as cur:
        for row in cur:
            rows.append(row)
    g = pd.DataFrame(rows, columns=fields)
    metrics["GWR"] = {"r2": r2_score(g["block_price"], g["PREDICTED"]), "rmse": np.sqrt(mean_squared_error(g["block_price"], g["PREDICTED"])), "mae": mean_absolute_error(g["block_price"], g["PREDICTED"])}
except Exception as exc:
    metrics["GWR"] = {"error": str(exc)}

Path(args.output_json).write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(metrics, ensure_ascii=False, indent=2))

