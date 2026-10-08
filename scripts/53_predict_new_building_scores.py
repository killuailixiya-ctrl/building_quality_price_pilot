from pathlib import Path
import hashlib
import pandas as pd
import numpy as np
import torch
from torch import nn
from torchvision import transforms, models
from PIL import Image

ROOT=Path(r'D:\Codex\building_01')
fix_dir=ROOT/'apps/building_comparison_fix_pic002/images'
ratings=pd.read_csv(ROOT/'data/processed/final_ratings.csv')
seg=pd.read_csv(ROOT/'images/image_building_segmentation.csv')

# 目标图片哈希
targets={}
for f in fix_dir.glob('*.jpg'):
    targets[hashlib.md5(f.read_bytes()).hexdigest()] = f.name

# 映射到 community_id
mapping={}
for _,row in seg.iterrows():
    if not targets:
        break
    src=Path(r'G:\huanghaojun_buliding\社区照片\img')/str(row['community_id'])/row['filename']
    if not src.exists():
        continue
    h=hashlib.md5(src.read_bytes()).hexdigest()
    if h in targets:
        mapping[targets.pop(h)] = {"community_id": int(row['community_id']), "source": row['filename']}
print('mapped', len(mapping))

# 加载模型
model=models.shufflenet_v2_x1_0(weights=None)
model.fc=nn.Linear(model.fc.in_features,1)
model.load_state_dict(torch.load(ROOT/'models/building_quality_shufflenet.pth', map_location='cpu'))
model.eval()

transform=transforms.Compose([
    transforms.Resize(256), transforms.CenterCrop(224), transforms.ToTensor(),
    transforms.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225]),
])

rows=[]
for pic_id, meta in mapping.items():
    img=Image.open(fix_dir/pic_id).convert('RGB')
    x=transform(img).unsqueeze(0)
    with torch.no_grad():
        score=float(model(x).item())
    rows.append({"pic_id": pic_id, "community_id": meta["community_id"], "source": meta["source"], "building_score_new": score})
out=pd.DataFrame(rows)
out.to_csv(ROOT/'data/processed/building_quality_new_scores.csv', index=False, encoding='utf-8-sig')
print(out.head())
print('saved', ROOT/'data/processed/building_quality_new_scores.csv')
