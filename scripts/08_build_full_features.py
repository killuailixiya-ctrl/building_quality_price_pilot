from __future__ import annotations
from pathlib import Path
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point

ROOT = Path(r"D:\Codex\building_01")
blocks_path = ROOT / "data/processed/wuhan_blocks.gdb"
comm_csv = ROOT / "data/processed/communities_geocoded.csv"
proxy_csv = ROOT / "images/image_efficientnet_scores.csv"
poi_csv = Path(r"E:\刘天辰\POI以及房价时序数据\POI武汉10-20\2021-湖北省-武汉市.csv")
metro_stations = Path(r"E:\刘天辰\武汉地铁数据\运行线路\武汉_站点.shp")
out_csv = ROOT / "data/processed/feature_matrix.csv"

CATEGORIES = {
    "kindergarten": ["幼儿园", "学前教育"],
    "primary": ["小学"],
    "junior": ["初中", "中学", "九年一贯制"],
    "university": ["大学", "学院", "高等教育"],
    "hospital_top": ["医院"],
    "basic_health": ["诊所", "药店", "卫生站", "社区卫生", "医疗保健"],
    "dining": ["餐饮"],
    "shopping": ["购物", "商场", "超市"],
    "leisure": ["休闲娱乐", "娱乐"],
    "company": ["公司企业"],
    "bus": ["公交"],
    "park": ["公园", "风景名胜", "绿地"],
}

blocks = gpd.read_file(blocks_path, layer="blocks").to_crs("EPSG:3857")
blocks = blocks[["block_id", "geometry"]].copy()
centroids = blocks.copy()
centroids["geometry"] = blocks.geometry.centroid

# communities -> block aggregate
comm = pd.read_csv(comm_csv)
comm = comm[(comm["lng"].notna()) & (comm["lat"].notna())].copy()
comm["geometry"] = [Point(x, y) for x, y in zip(comm["lng"], comm["lat"])]
comm_gdf = gpd.GeoDataFrame(comm, geometry="geometry", crs="EPSG:4326").to_crs("EPSG:3857")
joined = gpd.sjoin(comm_gdf, blocks, how="inner", predicate="within")
num_cols = ["price_yuan_m2", "age_years", "floor_area_ratio", "property_fee"]
feats = joined.groupby("block_id").agg(
    community_count=("community_id", "nunique"),
    **{("block_price" if c == "price_yuan_m2" else "block_" + c): (c, "mean") for c in num_cols}
).reset_index()

if proxy_csv.exists():
    proxy = pd.read_csv(proxy_csv)
    pc = proxy.groupby("community_id").agg(
        building_score_mean=("efficientnet_quality", "mean"),
        building_score_std=("efficientnet_quality", "std"),
        building_image_count=("efficientnet_quality", "size"),
    ).reset_index()
    joined_pc = joined[["block_id", "community_id"]].drop_duplicates().merge(pc, on="community_id", how="left")
    pb = joined_pc.groupby("block_id").agg(
        building_score_mean=("building_score_mean", "mean"),
        building_score_std=("building_score_std", "mean"),
        building_image_count=("building_image_count", "sum"),
    ).reset_index()
    feats = feats.merge(pb, on="block_id", how="left")

# POI features
chunks = []
reader = pd.read_csv(poi_csv, usecols=["类型1", "类型2", "类型3", "火星X", "火星Y"], chunksize=200000, encoding="gb18030")
for chunk in reader:
    t1 = (chunk["类型1"].astype(str) + ";" + chunk["类型2"].astype(str) + ";" + chunk["类型3"].astype(str))
    x = pd.to_numeric(chunk["火星X"], errors="coerce")
    y = pd.to_numeric(chunk["火星Y"], errors="coerce")
    valid = x.notna() & y.notna()
    for cat, patterns in CATEGORIES.items():
        mask = np.zeros(len(chunk), dtype=bool)
        for pat in patterns:
            mask |= t1.str.contains(pat, na=False)
        mask &= valid
        if mask.any():
            sub = pd.DataFrame({"cat": cat, "x": x[mask], "y": y[mask]})
            chunks.append(sub)
poi = pd.concat(chunks, ignore_index=True)
poi["geometry"] = [Point(x, y) for x, y in zip(poi["x"], poi["y"])]
poi_gdf = gpd.GeoDataFrame(poi, geometry="geometry", crs="EPSG:4326").to_crs("EPSG:3857")

for cat in CATEGORIES:
    sub = poi_gdf[poi_gdf["cat"] == cat].copy()
    if sub.empty:
        continue
    # count inside block
    cnt = gpd.sjoin(blocks, sub, how="left", predicate="contains").groupby("block_id").size().rename(f"{cat}_count")
    feats[f"{cat}_count"] = feats["block_id"].map(cnt).fillna(0)
    # nearest distance from centroid
    near = gpd.sjoin_nearest(centroids, sub, how="left", distance_col="dist", max_distance=30000)
    near = near.groupby("block_id")["dist"].min().rename(f"{cat}_dist")
    feats[f"{cat}_dist"] = feats["block_id"].map(near)

# metro
if metro_stations.exists():
    metro = gpd.read_file(metro_stations).to_crs("EPSG:3857")
    near_metro = gpd.sjoin_nearest(centroids, metro, how="left", distance_col="metro_dist", max_distance=50000)
    near_metro = near_metro.groupby("block_id")["metro_dist"].min().rename("metro_dist")
    feats["metro_dist"] = feats["block_id"].map(near_metro)
else:
    feats["metro_dist"] = np.nan

# location
feats["centroid_x"] = feats["block_id"].map(centroids.set_index("block_id").geometry.x)
feats["centroid_y"] = feats["block_id"].map(centroids.set_index("block_id").geometry.y)
feats.to_csv(out_csv, index=False, encoding="utf-8-sig")
print("full feature rows:", len(feats))
print("columns:", feats.columns.tolist())
print("written:", out_csv)



