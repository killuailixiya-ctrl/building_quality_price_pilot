from pathlib import Path
import arcpy
import pandas as pd

ROOT = Path(r"D:\Codex\building_01")
gdb = str(ROOT / "data/processed/paper_features.gdb")
blocks = pd.DataFrame([(r[0],) for r in arcpy.da.SearchCursor(str(ROOT/"data/processed/wuhan_blocks.gdb/blocks"), ["block_id"])], columns=["block_id"])

kde_cats = ["kindergarten","basic_health","dining","shopping","leisure","company","bus"]
for cat in kde_cats:
    table = f"{gdb}\\zonal_{cat}_kde"
    mapping = {r[0]: r[1] for r in arcpy.da.SearchCursor(table, ["block_id","MEAN"])}
    blocks[f"{cat}_kde"] = blocks["block_id"].map(mapping)

dist_cats = ["primary","junior","university","hospital_top","park"]
for cat in dist_cats:
    fc = f"{gdb}\\centroids_near_{cat}"
    mapping = {r[0]: r[1] for r in arcpy.da.SearchCursor(fc, ["block_id","NEAR_DIST"])}
    blocks[f"{cat}_dist"] = blocks["block_id"].map(mapping)

base = pd.read_csv(ROOT/"data/processed/feature_matrix.csv")
cols = ["block_id","block_price","building_score_mean","ndvi_mean","ndvi_std","green_ratio","water_ratio","ring3_dist_signed","centroid_x","centroid_y"]
for c in cols:
    if c not in base.columns:
        continue
blocks = blocks.merge(base[cols], on="block_id", how="left")
out = ROOT/"data/processed/feature_matrix_paper_style.csv"
blocks.to_csv(out, index=False, encoding="utf-8-sig")
print("rows", len(blocks))
print("columns", blocks.columns.tolist())
print("written", out)
