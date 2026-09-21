from pathlib import Path
import pandas as pd, hashlib, shutil
ROOT=Path(r'D:\Codex\building_01')
site=ROOT/'apps/building_comparison_fix'
existing=set()
for f in (site/'images').glob('*.jpg'):
    existing.add(hashlib.md5(f.read_bytes()).hexdigest())
seg=pd.read_csv(ROOT/'images/image_building_segmentation.csv')
seg=seg[(seg['is_building_likely']==1)&(seg['building_ratio']>=0.20)].copy()
for _,row in seg.iterrows():
    src=Path(r'G:\huanghaojun_buliding\社区照片\img')/str(row['community_id'])/row['filename']
    if not src.exists(): continue
    b=src.read_bytes()
    if len(b)==36426: continue
    h=hashlib.md5(b).hexdigest()
    if h in existing: continue
    shutil.copyfile(src, site/'images/pic_002.jpg')
    print('replaced', src)
    break
