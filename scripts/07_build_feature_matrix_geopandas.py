from __future__ import annotations
import sys
from pathlib import Path
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

ROOT = Path(r"D:\Codex\building_01")
comm_csv = ROOT / "data/processed/communities_geocoded.csv"
proxy_csv = ROOT / "images/image_proxy_scores.csv"
blocks_path = ROOT / "data/processed/wuhan_blocks.gdb"
out_csv = ROOT / "data/processed/feature_matrix.csv"

blocks = gpd.read_file(blocks_path, layer="blocks")
blocks = blocks[["block_id", "geometry"]].copy()

comm = pd.read_csv(comm_csv)
comm = comm[(comm["lng"].notna()) & (comm["lat"].notna())].copy()
comm["geometry"] = [Point(x, y) for x, y in zip(comm["lng"], comm["lat"])]
comm_gdf = gpd.GeoDataFrame(comm, geometry="geometry", crs="EPSG:4326").to_crs(blocks.crs)

joined = gpd.sjoin(comm_gdf, blocks[["block_id", "geometry"]], how="inner", predicate="within")
num_cols = ["price_yuan_m2", "age_years", "floor_area_ratio", "property_fee"]
block_feats = joined.groupby("block_id").agg(
    community_count=("community_id", "nunique"),
    **{f"block_{c if c != 'price_yuan_m2' else 'price'}": (c, "mean") for c in num_cols}
).reset_index()
block_feats.rename(columns={"block_price_yuan_m2": "block_price"}, inplace=True)

if proxy_csv.exists():
    proxy = pd.read_csv(proxy_csv)
    proxy_comm = proxy.groupby("community_id").agg(
        building_score_mean=("quality_proxy", "mean"),
        building_score_std=("quality_proxy", "std"),
        image_count=("quality_proxy", "size"),
    ).reset_index()
    joined2 = joined[["block_id", "community_id"]].drop_duplicates().merge(proxy_comm, on="community_id", how="left")
    proxy_block = joined2.groupby("block_id").agg(
        building_score_mean=("building_score_mean", "mean"),
        building_score_std=("building_score_std", "mean"),
        building_image_count=("image_count", "sum"),
    ).reset_index()
    block_feats = block_feats.merge(proxy_block, on="block_id", how="left")
else:
    print("image_proxy_scores.csv not found; skipping building score")

block_feats = block_feats.merge(blocks[["block_id", "geometry"]], on="block_id", how="left")
block_feats["centroid_x"] = block_feats["geometry"].apply(lambda g: g.centroid.x)
block_feats["centroid_y"] = block_feats["geometry"].apply(lambda g: g.centroid.y)
block_feats = block_feats.drop(columns="geometry")
block_feats.to_csv(out_csv, index=False, encoding="utf-8-sig")
print("feature_matrix rows:", len(block_feats))
print("columns:", block_feats.columns.tolist())
print("written:", out_csv)


