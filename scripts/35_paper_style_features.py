from __future__ import annotations
from pathlib import Path
import arcpy
import pandas as pd
import numpy as np
from arcpy.sa import KernelDensity, ZonalStatisticsAsTable, Idw

arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("Spatial")

ROOT = Path(r"D:\Codex\building_01")
blocks = str(ROOT / "data/processed/wuhan_blocks.gdb/blocks")
communities = str(ROOT / "data/processed/wuhan_features.gdb/communities_projected")
out_gdb = str(ROOT / "data/processed/paper_features.gdb")
if not arcpy.Exists(out_gdb):
    arcpy.management.CreateFileGDB(str(ROOT / "data/processed"), "paper_features.gdb")

# 街区质心
centroids = out_gdb + "\\centroids"
arcpy.management.FeatureToPoint(blocks, centroids, "INSIDE")

# 读取并分类 2021 POI
poi_csv = r"G:\huanghaojun_buliding\POI以及房价时序数据\POI武汉10-20\2021-湖北省-武汉市.csv"
categories = {
    "kindergarten": ["幼儿园","学前教育"],
    "basic_health": ["诊所","药店","卫生站","社区卫生","医疗保健"],
    "dining": ["餐饮"],
    "shopping": ["购物","商场","超市"],
    "leisure": ["休闲娱乐","娱乐"],
    "company": ["公司企业"],
    "bus": ["公交"],
    "primary": ["小学"],
    "junior": ["初中","中学","九年一贯制"],
    "university": ["大学","学院","高等教育"],
    "hospital_top": ["医院"],
    "park": ["公园","风景名胜","绿地"],
}
kde_cats = ["kindergarten","basic_health","dining","shopping","leisure","company","bus"]
dist_cats = ["primary","junior","university","hospital_top","park"]

# 创建点要素类并写入分类点
for cat in categories:
    fc = out_gdb + f"\\poi_{cat}"
    if arcpy.Exists(fc): arcpy.management.Delete(fc)
    arcpy.management.CreateFeatureclass(out_gdb, f"poi_{cat}", "POINT", spatial_reference=arcpy.SpatialReference(4326))
    arcpy.management.AddField(fc, "cat", "TEXT", field_length=32)

pending = {cat: [] for cat in categories}
reader = pd.read_csv(poi_csv, usecols=["类型1","类型2","类型3","火星X","火星Y"], chunksize=200000, encoding="gb18030")
for chunk in reader:
    t = chunk["类型1"].astype(str)+";"+chunk["类型2"].astype(str)+";"+chunk["类型3"].astype(str)
    x = pd.to_numeric(chunk["火星X"], errors="coerce")
    y = pd.to_numeric(chunk["火星Y"], errors="coerce")
    valid = x.notna() & y.notna()
    for cat, patterns in categories.items():
        mask = np.zeros(len(chunk), dtype=bool)
        for pat in patterns:
            mask |= t.str.contains(pat, na=False)
        mask &= valid
        if mask.any():
            for xi, yi in zip(x[mask], y[mask]):
                pending[cat].append((float(xi), float(yi)))

# 逐个类别写入点，避免同一工作空间多个 InsertCursor 同时打开
for cat, rows in pending.items():
    fc = out_gdb + f"\\poi_{cat}"
    with arcpy.da.InsertCursor(fc, ["SHAPE@", "cat"]) as cur:
        for xi, yi in rows:
            cur.insertRow([arcpy.Point(xi, yi), cat])

# KDE -> 分区均值
kde_features = {}
for cat in kde_cats:
    fc = out_gdb + f"\\poi_{cat}"
    kde = KernelDensity(fc, "NONE", cell_size=500, search_radius=2000, area_unit_scale_factor="SQUARE_KILOMETERS")
    kde.save(out_gdb + f"\\kde_{cat}")
    table = out_gdb + f"\\zonal_{cat}_kde"
    ZonalStatisticsAsTable(blocks, "block_id", out_gdb + f"\\kde_{cat}", table, "DATA", "MEAN")
    kde_features[cat] = table

# 最近距离
dist_features = {}
for cat in dist_cats:
    fc = out_gdb + f"\\poi_{cat}"
    near_centroids = out_gdb + f"\\centroids_near_{cat}"
    arcpy.management.CopyFeatures(centroids, near_centroids)
    arcpy.analysis.Near(near_centroids, fc, search_radius=50000, location="NO_LOCATION")
    dist_features[cat] = near_centroids

print("done creating paper-style GIS features")
print("gdb", out_gdb)
