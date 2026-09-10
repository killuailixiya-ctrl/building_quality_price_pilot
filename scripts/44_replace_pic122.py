from pathlib import Path
import pandas as pd, hashlib, shutil
ROOT=Path(r'D:\Codex\building_01')
web=ROOT/'apps/building_comparison_web/images'
current=set()
for f in web.glob('*.jpg'):
    current.add(hashlib.md5(f.read_bytes()).hexdigest())
seg=pd.read_csv(ROOT/'images/image_building_segmentation.csv')
# 提高建筑图阈值，避免低建筑占比的非建筑图
seg=seg[(seg['is_building_likely']==1) & (seg['building_ratio']>=0.20)].copy()
replacement=None
for _,row in seg.iterrows():
    src=Path(r'G:\huanghaojun_buliding\社区照片\img')/str(row['community_id'])/row['filename']
    if not src.exists(): continue
    b=src.read_bytes()
    if len(b)==36426: continue
    h=hashlib.md5(b).hexdigest()
    if h in current: continue
    replacement=(src,h)
    break
if replacement:
    dst=web/'pic_122.jpg'
    shutil.copyfile(replacement[0], dst)
    print('replaced pic_122 with', replacement[0])
else:
    print('no replacement')
