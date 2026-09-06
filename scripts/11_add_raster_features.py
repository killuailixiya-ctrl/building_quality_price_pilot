from __future__ import annotations
from pathlib import Path
import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import rasterize

ROOT = Path(r"D:\Codex\building_01")
blocks_path = ROOT / "data/processed/wuhan_blocks.gdb"
feature_csv = ROOT / "data/processed/feature_matrix.csv"
ndvi_path = Path(r"G:\huanghaojun_buliding\武汉NDVI\武汉202305ndvi\ndviwh202305.tif")
landcover_path = Path(r"G:\huanghaojun_buliding\土地覆盖类型\2020武汉市.tif")

GREEN_CLASSES = {20, 30, 50}
WATER_CLASSES = {60}

blocks = gpd.read_file(blocks_path, layer="blocks").to_crs("EPSG:4326")
blocks["id_int"] = range(1, len(blocks) + 1)
id_to_block = dict(zip(blocks["id_int"], blocks["block_id"]))

shapes = [(geom, int_id) for geom, int_id in zip(blocks.geometry, blocks["id_int"])]

def rasterize_blocks(raster_path):
    with rasterio.open(raster_path) as src:
        arr = src.read(1).astype(np.float32)
        transform = src.transform
        shape = arr.shape
        id_arr = rasterize(shapes, out_shape=shape, transform=transform, fill=0, dtype="int32")
        return arr, id_arr, shape

rows = {}
for int_id in blocks["id_int"]:
    rows[int_id] = {"block_id": id_to_block[int_id]}

ndvi, ndvi_ids, _ = rasterize_blocks(ndvi_path)
land, land_ids, _ = rasterize_blocks(landcover_path)

for int_id in blocks["id_int"]:
    mask = ndvi_ids == int_id
    if mask.any():
        vals = ndvi[mask]
        rows[int_id]["ndvi_mean"] = float(np.nanmean(vals))
        rows[int_id]["ndvi_std"] = float(np.nanstd(vals))
    else:
        rows[int_id]["ndvi_mean"] = np.nan
        rows[int_id]["ndvi_std"] = np.nan

    mask = land_ids == int_id
    if mask.any():
        vals = land[mask]
        total = vals.size
        green = float(np.isin(vals, list(GREEN_CLASSES)).sum() / total)
        water = float(np.isin(vals, list(WATER_CLASSES)).sum() / total)
        rows[int_id]["green_ratio"] = green
        rows[int_id]["water_ratio"] = water
    else:
        rows[int_id]["green_ratio"] = np.nan
        rows[int_id]["water_ratio"] = np.nan

raster_feats = pd.DataFrame.from_dict(rows, orient="index").reset_index(drop=True)
feats = pd.read_csv(feature_csv)
feats = feats.drop(columns=[c for c in ["ndvi_mean", "ndvi_std", "green_ratio", "water_ratio"] if c in feats.columns])
feats = feats.merge(raster_feats, on="block_id", how="left")
feats.to_csv(feature_csv, index=False, encoding="utf-8-sig")
print("rows:", len(feats))
print("raster columns added:", ["ndvi_mean", "ndvi_std", "green_ratio", "water_ratio"])
print("coverage ndvi:", feats["ndvi_mean"].notna().sum(), "water:", feats["water_ratio"].notna().sum())


