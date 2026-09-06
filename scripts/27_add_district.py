from __future__ import annotations
from pathlib import Path
import geopandas as gpd
import pandas as pd
import numpy as np

ROOT = Path(r"D:\Codex\building_01")
blocks = gpd.read_file(ROOT / "data/processed/wuhan_blocks.gdb", layer="blocks").to_crs("EPSG:3857")
blocks = blocks[["block_id", "geometry"]].copy()
centroids = blocks.copy()
centroids["geometry"] = blocks.geometry.centroid

districts = gpd.read_file(r"G:\huanghaojun_buliding\行政区划\行政区划\武汉市_区县.shp").to_crs("EPSG:3857")
districts = districts[["地名", "geometry"]].rename(columns={"地名": "district"})
joined = gpd.sjoin(centroids, districts, how="left", predicate="within")
block_district = joined[["block_id", "district"]].drop_duplicates(subset=["block_id"])

df = pd.read_csv(ROOT / "data/processed/multiyear_lishi_feature_matrix.csv")
df = df.merge(block_district, on="block_id", how="left")
out = ROOT / "data/processed/multiyear_lishi_with_district.csv"
df.to_csv(out, index=False, encoding="utf-8-sig")
print(df.groupby("district").size())
print("written", out)
