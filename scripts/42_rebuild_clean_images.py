from pathlib import Path
import pandas as pd
import shutil
import hashlib

ROOT = Path(r"D:\Codex\building_01")
seg = pd.read_csv(ROOT / "images/image_building_segmentation.csv")
seg = seg[seg["is_building_likely"] == 1].copy()

rows=[]
for _, row in seg.iterrows():
    src = Path(r"G:\huanghaojun_buliding\社区照片\img") / str(row["community_id"]) / row["filename"]
    if not src.exists():
        continue
    b = src.read_bytes()
    rows.append({
        "community_id": int(row["community_id"]),
        "filename": row["filename"],
        "building_ratio": row["building_ratio"],
        "bytes": len(b),
        "md5": hashlib.md5(b).hexdigest(),
        "src": src,
    })

df = pd.DataFrame(rows)
# 排除疑似占位图：1200x900 且文件大小固定的常见占位图
df = df[df["bytes"] != 36426].copy()
# 每个小区最多保留一张
df = df.drop_duplicates(subset=["community_id"])
# 去除完全相同图片
df = df.drop_duplicates(subset=["md5"])
df["bins"] = pd.qcut(df["building_ratio"].rank(method="first"), q=5, labels=False)
sample = df.groupby("bins", group_keys=False).apply(lambda x: x.sample(n=min(len(x),40), random_state=42)).reset_index(drop=True)
if len(sample) > 200:
    sample = sample.sample(200, random_state=42).reset_index(drop=True)

web = ROOT / "apps/building_comparison_web/images"
for f in web.glob("*"):
    if f.is_file():
        f.unlink()
rows_out=[]
for i, row in sample.iterrows():
    dst = web / f"pic_{i:03d}.jpg"
    shutil.copyfile(row["src"], dst)
    rows_out.append({"id": dst.name, "pic_id": dst.name, "url": f"images/{dst.name}"})
import json
(web.parent / "images_manifest.json").write_text(json.dumps(rows_out, ensure_ascii=False), encoding="utf-8")
print("selected", len(rows_out))
