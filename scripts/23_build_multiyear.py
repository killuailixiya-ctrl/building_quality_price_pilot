from __future__ import annotations
from pathlib import Path
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point

ROOT = Path(r"D:\Codex\building_01")
blocks_path = ROOT / "data/processed/wuhan_blocks.gdb"
feat_2022 = pd.read_csv(ROOT / "data/processed/feature_matrix.csv")
blocks = gpd.read_file(blocks_path, layer="blocks").to_crs("EPSG:3857")
blocks = blocks[["block_id", "geometry"]].copy()

def point_frame(lng_series, lat_series, value_series, year):
    df = pd.DataFrame({
        "lng": pd.to_numeric(lng_series, errors="coerce"),
        "lat": pd.to_numeric(lat_series, errors="coerce"),
        "block_price": pd.to_numeric(value_series, errors="coerce"),
        "year": year,
    })
    df = df[(df["lng"].notna()) & (df["lat"].notna()) & (df["block_price"].notna())]
    df["geometry"] = [Point(x, y) for x, y in zip(df["lng"], df["lat"])]
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326").to_crs("EPSG:3857")
    joined = gpd.sjoin(gdf, blocks, how="inner", predicate="within")
    agg = joined.groupby("block_id").agg(block_price=("block_price", "mean"), n=("block_price", "size")).reset_index()
    agg["year"] = year
    return agg

# 2022 baseline
base = feat_2022[["block_id", "block_price", "building_score_mean", "building_score_std", "building_image_count", "centroid_x", "centroid_y"]].copy()
base["year"] = 2022

# 2018
x2018 = pd.read_excel(r"G:\huanghaojun_buliding\01熊秀海\03-房价数据\05房价数据\2018房价\武汉小区数据.xlsx")
y2018 = point_frame(x2018["经度_WGS1984坐标"], x2018["纬度_WGS1984坐标"], x2018["均价"], 2018)

# 2017
g2017 = gpd.read_file(r"G:\huanghaojun_buliding\01熊秀海\03-房价数据\05房价数据\2017年房价\房价.shp")
y2017 = point_frame(g2017["经度"], g2017["纬度"], g2017["挂牌单"], 2017)

base_score = feat_2022[["block_id", "building_score_mean", "building_image_count", "centroid_x", "centroid_y"]].drop_duplicates(subset=["block_id"])
for ydf in [y2018, y2017]:
    ydf = ydf.merge(base_score, on="block_id", how="left")
    ydf = ydf[["block_id", "block_price", "building_score_mean", "building_image_count", "centroid_x", "centroid_y", "year"]]
    base = pd.concat([base, ydf], ignore_index=True)

base.to_csv(ROOT / "data/processed/multiyear_feature_matrix.csv", index=False, encoding="utf-8-sig")
print(base.groupby("year").size())
print(base.groupby("year")["block_price"].describe())
print("written", ROOT / "data/processed/multiyear_feature_matrix.csv")
