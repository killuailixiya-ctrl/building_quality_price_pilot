from __future__ import annotations
from pathlib import Path
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point

ROOT = Path(r"D:\Codex\building_01")
blocks = gpd.read_file(ROOT / "data/processed/wuhan_blocks.gdb", layer="blocks").to_crs("EPSG:3857")[["block_id","geometry"]].copy()
centroids = blocks.copy(); centroids["geometry"] = blocks.geometry.centroid

CATEGORIES = {
    "kindergarten": ["幼儿园","学前教育"],
    "primary": ["小学"],
    "junior": ["初中","中学","九年一贯制"],
    "university": ["大学","学院","高等教育"],
    "hospital_top": ["医院"],
    "basic_health": ["诊所","药店","卫生站","社区卫生","医疗保健"],
    "dining": ["餐饮"],
    "shopping": ["购物","商场","超市"],
    "leisure": ["休闲娱乐","娱乐"],
    "company": ["公司企业"],
    "bus": ["公交"],
    "park": ["公园","风景名胜","绿地"],
}

def process_year(year, csv_path):
    chunks = []
    reader = pd.read_csv(csv_path, usecols=["类型1","类型2","类型3","火星X","火星Y"], chunksize=200000, encoding="gb18030")
    for chunk in reader:
        t = chunk["类型1"].astype(str)+";"+chunk["类型2"].astype(str)+";"+chunk["类型3"].astype(str)
        x = pd.to_numeric(chunk["火星X"], errors="coerce")
        y = pd.to_numeric(chunk["火星Y"], errors="coerce")
        valid = x.notna() & y.notna()
        for cat, patterns in CATEGORIES.items():
            mask = np.zeros(len(chunk), dtype=bool)
            for pat in patterns:
                mask |= t.str.contains(pat, na=False)
            mask &= valid
            if mask.any():
                chunks.append(pd.DataFrame({"cat":cat,"x":x[mask],"y":y[mask]}))
    poi = pd.concat(chunks, ignore_index=True)
    poi["geometry"] = [Point(x,y) for x,y in zip(poi.x, poi.y)]
    poi = gpd.GeoDataFrame(poi, geometry="geometry", crs="EPSG:4326").to_crs("EPSG:3857")
    feats = {"block_id": blocks["block_id"], "year": year}
    for cat in CATEGORIES:
        sub = poi[poi["cat"]==cat].copy()
        if sub.empty:
            feats[f"{cat}_count"] = 0.0
            feats[f"{cat}_dist"] = np.nan
            continue
        cnt = gpd.sjoin(blocks, sub, how="left", predicate="contains").groupby("block_id").size()
        feats[f"{cat}_count"] = blocks["block_id"].map(cnt).fillna(0)
        near = gpd.sjoin_nearest(centroids, sub, how="left", distance_col="dist", max_distance=30000).groupby("block_id")["dist"].min()
        feats[f"{cat}_dist"] = blocks["block_id"].map(near)
    return pd.DataFrame(feats)

frames=[]
for year in range(2017,2023):
    src_year = year if year <= 2021 else 2021
    path = Path(rf"G:\huanghaojun_buliding\POI以及房价时序数据\POI武汉10-20\{src_year}-湖北省-武汉市.csv")
    print("processing", year, "using", src_year)
    frames.append(process_year(year, path))

out = pd.concat(frames, ignore_index=True)
out.to_csv(ROOT / "data/processed/dynamic_poi_features.csv", index=False, encoding="utf-8-sig")
print(out.groupby("year").size())
print("written", ROOT / "data/processed/dynamic_poi_features.csv")
