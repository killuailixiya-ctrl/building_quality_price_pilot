from __future__ import annotations
from pathlib import Path
import arcpy
import pandas as pd
import numpy as np
from pyproj import Transformer

ROOT = Path(r"D:\Codex\building_01")
feat_csv = ROOT / "data/processed/feature_matrix.csv"
gdb = str(ROOT / "data/processed/wuhan_features.gdb")
df = pd.read_csv(feat_csv)

# 用 ArcGIS IDW 分区统计替换简单均值
for table, new_col, old_col in [
    ("zonal_block_price_v2", "block_price", "block_price"),
    ("zonal_block_age", "block_age_years", "block_age_years"),
    ("zonal_block_far", "block_floor_area_ratio", "block_floor_area_ratio"),
]:
    rows = []
    path = f"{gdb}\\{table}"
    with arcpy.da.SearchCursor(path, ["block_id", "MEAN"]) as cur:
        for row in cur:
            rows.append((str(row[0]), float(row[1])))
    mapping = dict(rows)
    df[new_col] = df["block_id"].map(mapping)

# 城市中心距离：武汉市政府附近，转为 Web Mercator
transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
cx, cy = transformer.transform(114.305, 30.593)
df["center_dist"] = np.sqrt((df["centroid_x"] - cx) ** 2 + (df["centroid_y"] - cy) ** 2)

df.to_csv(feat_csv, index=False, encoding="utf-8-sig")
print("rows", len(df))
print("block_price describe")
print(df["block_price"].describe())
print("center_dist describe")
print(df["center_dist"].describe())
print("written", feat_csv)

