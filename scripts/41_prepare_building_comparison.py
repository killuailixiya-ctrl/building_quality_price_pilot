from pathlib import Path
import pandas as pd
import shutil

ROOT = Path(r"D:\Codex\building_01")
seg = pd.read_csv(ROOT / "images/image_building_segmentation.csv")
seg = seg[seg["is_building_likely"] == 1].copy()
# 每个小区最多保留1张，避免同一小区图片过多
seg = seg.drop_duplicates(subset=["community_id"])
# 按 building_ratio 分层抽样200张
seg["bins"] = pd.qcut(seg["building_ratio"].rank(method="first"), q=5, labels=False)
sample = seg.groupby("bins", group_keys=False).apply(lambda x: x.sample(n=min(len(x),40), random_state=42)).reset_index(drop=True)
if len(sample) > 200:
    sample = sample.sample(200, random_state=42).reset_index(drop=True)

app_dir = ROOT / "apps/building_comparison"
img_dir = app_dir / "images"
img_dir.mkdir(parents=True, exist_ok=True)
rows=[]
for i, row in sample.iterrows():
    src = Path(r"G:\huanghaojun_buliding\社区照片\img") / str(row["community_id"]) / row["filename"]
    if not src.exists():
        continue
    new_name = f"pic_{i:03d}.jpg"
    dst = img_dir / new_name
    shutil.copyfile(src, dst)
    rows.append({"pic_id": new_name, "community_id": int(row["community_id"]), "source": row["filename"]})

manifest = pd.DataFrame(rows)
manifest.to_csv(app_dir / "images_manifest.csv", index=False, encoding="utf-8-sig")
print("selected", len(manifest), "images")
print("saved", app_dir / "images_manifest.csv")
