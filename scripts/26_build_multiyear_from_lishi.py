from __future__ import annotations
from pathlib import Path
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point

ROOT = Path(r"D:\Codex\building_01")
blocks_path = ROOT / "data/processed/wuhan_blocks.gdb"
base_dir = Path(r"G:\huanghaojun_buliding\01熊秀海\03-房价数据\05房价数据\安居客房价202209\lishi")
comm = pd.read_csv(ROOT / "data/processed/communities_geocoded.csv")
score = pd.read_csv(ROOT / "images/image_efficientnet_scores.csv").groupby("community_id")["efficientnet_quality"].mean().rename("building_score_mean").reset_index()
comm = comm[["community_id", "lng", "lat"]].dropna().merge(score, on="community_id", how="left")

blocks = gpd.read_file(blocks_path, layer="blocks").to_crs("EPSG:3857")[["block_id", "geometry"]]

def to_blocks(ydf):
    gdf = gpd.GeoDataFrame(ydf, geometry=gpd.points_from_xy(ydf["lng"], ydf["lat"]), crs="EPSG:4326").to_crs("EPSG:3857")
    joined = gpd.sjoin(gdf, blocks, how="inner", predicate="within")
    agg = joined.groupby("block_id").agg(block_price=("price", "mean"), building_score_mean=("building_score_mean", "mean"), n=("price", "size")).reset_index()
    return agg

frames = []
for year in range(2017, 2023):
    p = base_dir / f"{year}.csv"
    if not p.exists():
        continue
    raw = pd.read_csv(p)
    price_cols = [f"y_{m:02d}" for m in range(1, 13)]
    raw = raw[(raw[price_cols] > 0).any(axis=1)].copy()
    raw["price"] = raw[price_cols].mean(axis=1)
    merged = raw[["community_id", "price"]].merge(comm, on="community_id", how="inner")
    block_agg = to_blocks(merged)
    block_agg["year"] = year
    frames.append(block_agg)

out = pd.concat(frames, ignore_index=True)
out["centroid_x"] = out["block_id"].map(blocks.set_index("block_id").geometry.centroid.x)
out["centroid_y"] = out["block_id"].map(blocks.set_index("block_id").geometry.centroid.y)
out.to_csv(ROOT / "data/processed/multiyear_lishi_feature_matrix.csv", index=False, encoding="utf-8-sig")
print(out.groupby("year").size())
print(out.groupby("year")["block_price"].describe())
print("written", ROOT / "data/processed/multiyear_lishi_feature_matrix.csv")
