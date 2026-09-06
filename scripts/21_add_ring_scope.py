from __future__ import annotations
from pathlib import Path
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point

ROOT = Path(r"D:\Codex\building_01")
feat_csv = ROOT / "data/processed/feature_matrix.csv"
ring_path = Path(r"E:\刘天辰\01熊秀海\05贵凯给的数据\武汉市边界、路网\环线_面.shp")

df = pd.read_csv(feat_csv)
rings = gpd.read_file(ring_path).to_crs("EPSG:3857")
# 假设 Id=3 为三环线。若换城市/数据，需要核对。
ring3 = rings[rings["Id"] == 3].geometry.iloc[0]
boundary = ring3.boundary

points = [Point(x, y) for x, y in zip(df["centroid_x"], df["centroid_y"])]
inside = np.array([p.within(ring3) for p in points])
dists = np.array([p.distance(boundary) for p in points])
# 内正外负，方便直接进入回归模型。
signed = np.where(inside, dists, -dists)
df["inside_ring3"] = inside.astype(int)
df["ring3_dist_signed"] = signed

df.to_csv(feat_csv, index=False, encoding="utf-8-sig")
inside_df = df[df["inside_ring3"] == 1].copy()
inside_csv = ROOT / "data/processed/feature_matrix_inside_ring3.csv"
inside_df.to_csv(inside_csv, index=False, encoding="utf-8-sig")

print("full rows", len(df), "inside_ring3", int(inside.sum()))
print("inside price describe")
print(inside_df["block_price"].describe())
print("written", inside_csv)
