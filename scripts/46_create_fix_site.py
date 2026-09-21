from pathlib import Path
import shutil, hashlib, json
import pandas as pd

ROOT = Path(r"D:\Codex\building_01")
src_site = ROOT / "apps/building_comparison_web"
dst_site = ROOT / "apps/building_comparison_fix"
dst_img = dst_site / "images"
if dst_site.exists():
    shutil.rmtree(dst_site)
dst_img.mkdir(parents=True)

# 复制旧网站图片，保持旧站不变
for f in (src_site / "images").glob("*.jpg"):
    shutil.copyfile(f, dst_img / f.name)

bad_ids = {"pic_122.jpg", "pic_103.jpg", "pic_012.jpg", "pic_124.jpg", "pic_146.jpg", "pic_105.jpg"}

# 现有图片哈希，用于找不重复的新图
existing_hashes = set()
for f in dst_img.glob("*.jpg"):
    existing_hashes.add(hashlib.md5(f.read_bytes()).hexdigest())

seg = pd.read_csv(ROOT / "images/image_building_segmentation.csv")
seg = seg[(seg["is_building_likely"] == 1) & (seg["building_ratio"] >= 0.20)].copy()
# 排除已经存在的哈希
seg = seg.drop_duplicates(subset=["community_id"]).reset_index(drop=True)

replacements = []
for _, row in seg.iterrows():
    src = Path(r"G:\huanghaojun_buliding\社区照片\img") / str(row["community_id"]) / row["filename"]
    if not src.exists():
        continue
    b = src.read_bytes()
    if len(b) == 36426:
        continue
    h = hashlib.md5(b).hexdigest()
    if h in existing_hashes:
        continue
    replacements.append((src, h))
    existing_hashes.add(h)
    if len(replacements) >= len(bad_ids):
        break

if len(replacements) < len(bad_ids):
    raise RuntimeError("合规替换图片不足")

for bad_id, (src, h) in zip(sorted(bad_ids), replacements):
    shutil.copyfile(src, dst_img / bad_id)

ids = sorted([f.name for f in dst_img.glob("*.jpg")])
pairs = []
for i in range(len(ids)):
    for j in range(i+1, len(ids)):
        if ids[i] in bad_ids or ids[j] in bad_ids:
            pairs.append([ids[i], ids[j]])

manifest = [{"id": name, "pic_id": name, "url": f"images/{name}"} for name in ids]
(dst_site / "images_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
(dst_site / "fix_pairs.json").write_text(json.dumps(pairs, ensure_ascii=False), encoding="utf-8")
print("images", len(ids), "fix_pairs", len(pairs))
print("replacements", list(zip(sorted(bad_ids), [str(x[0]) for x in replacements])))
