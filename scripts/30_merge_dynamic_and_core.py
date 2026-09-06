from pathlib import Path
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point

ROOT = Path(r"D:\Codex\building_01")
base = pd.read_csv(ROOT / "data/processed/multiyear_lishi_with_district.csv")
poi = pd.read_csv(ROOT / "data/processed/dynamic_poi_features.csv")
merged = base.merge(poi, on=["block_id","year"], how="left")

# 当前运行线路地铁距离，作为近似；严格的逐年地铁需要开通年份表。
metro = gpd.read_file(r"G:\huanghaojun_buliding\武汉地铁数据\运行线路\武汉_站点.shp").to_crs("EPSG:3857")
blocks = gpd.read_file(ROOT / "data/processed/wuhan_blocks.gdb", layer="blocks").to_crs("EPSG:3857")[["block_id","geometry"]].copy()
centroids = blocks.copy(); centroids["geometry"] = blocks.geometry.centroid
near = gpd.sjoin_nearest(centroids, metro, how="left", distance_col="dist", max_distance=50000).groupby("block_id")["dist"].min().rename("metro_dist_current")
merged["metro_dist_current"] = merged["block_id"].map(near)

rings = gpd.read_file(r"G:\huanghaojun_buliding\01熊秀海\05贵凯给的数据\武汉市边界、路网\环线_面.shp").to_crs("EPSG:3857")
ring3 = rings[rings["Id"]==3].geometry.iloc[0]
points = [Point(x,y) for x,y in zip(merged["centroid_x"], merged["centroid_y"])]
merged["inside_ring3"] = np.array([p.within(ring3) for p in points]).astype(int)

full_out = ROOT / "data/processed/multiyear_final_full.csv"
core_out = ROOT / "data/processed/multiyear_final_core.csv"
merged.to_csv(full_out, index=False, encoding="utf-8-sig")
merged[merged["inside_ring3"]==1].to_csv(core_out, index=False, encoding="utf-8-sig")
print("full", len(merged), "core", int(merged["inside_ring3"].sum()))
print("written", full_out, core_out)
