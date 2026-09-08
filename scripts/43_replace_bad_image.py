from pathlib import Path
import pandas as pd, hashlib, shutil, json
ROOT=Path(r'D:\Codex\building_01')
web=ROOT/'apps/building_comparison_web/images'
# 现有图片md5
current_hashes=set()
for f in web.glob('*.jpg'):
    current_hashes.add(hashlib.md5(f.read_bytes()).hexdigest())
seg=pd.read_csv(ROOT/'images/image_building_segmentation.csv')
seg=seg[seg['is_building_likely']==1].copy()
# 找新候选
replacement=None
for _,row in seg.iterrows():
    src=Path(r'G:\huanghaojun_buliding\社区照片\img')/str(row['community_id'])/row['filename']
    if not src.exists(): continue
    b=src.read_bytes()
    if len(b)==36426: continue
    h=hashlib.md5(b).hexdigest()
    if h in current_hashes: continue
    replacement=(src,h)
    break
if replacement:
    dst=web/'pic_154.jpg'
    shutil.copyfile(replacement[0], dst)
    current_hashes.add(replacement[1])
    print('replaced with', replacement[0])
else:
    print('no replacement found')
