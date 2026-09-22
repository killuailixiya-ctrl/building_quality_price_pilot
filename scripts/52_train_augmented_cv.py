from pathlib import Path
import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, models
from PIL import Image
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score

ROOT=Path(r'D:\Codex\building_01')
ratings=pd.read_csv(ROOT/'data/processed/final_ratings.csv').reset_index(drop=True)
img_dir=ROOT/'apps/building_comparison_fix_pic002/images'

train_transform=transforms.Compose([
    transforms.RandomResizedCrop(224, scale=(0.75,1.0)),
    transforms.RandomHorizontalFlip(),
    transforms.ColorJitter(brightness=0.2, contrast=0.2),
    transforms.ToTensor(),
    transforms.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225]),
])
val_transform=transforms.Compose([
    transforms.Resize(256), transforms.CenterCrop(224), transforms.ToTensor(),
    transforms.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225]),
])

class DS(Dataset):
    def __init__(self, df, root, transform):
        self.df=df.reset_index(drop=True); self.root=Path(root); self.transform=transform
    def __len__(self): return len(self.df)
    def __getitem__(self,i):
        row=self.df.iloc[i]
        img=Image.open(self.root/row['pic_id']).convert('RGB')
        return self.transform(img), float(row['trueskill.score'])

device='cpu'
kf=KFold(n_splits=2, shuffle=True, random_state=42)
fold_r2=[]; best_state=None; best_r2=-np.inf
for fold,(tr_idx,va_idx) in enumerate(kf.split(ratings),1):
    model=torch.load(r"G:\huanghaojun_buliding\08街景主观感知\model_results_20250924_104638_质量_EfficientNet_300_200\best_model_质量.pth", map_location=device, weights_only=False)
    model.classifier=nn.Sequential(nn.Dropout(0.2), nn.Linear(1280,1))
    model=model.to(device)
    opt=torch.optim.Adam(model.parameters(), lr=5e-5)
    crit=nn.MSELoss()
    tr_ds=DS(ratings.iloc[tr_idx],img_dir,train_transform)
    va_ds=DS(ratings.iloc[va_idx],img_dir,val_transform)
    tr=DataLoader(tr_ds,batch_size=16,shuffle=True); va=DataLoader(va_ds,batch_size=16)
    for epoch in range(1,16):
        model.train()
        for x,y in tr:
            x=x.to(device); y=y.to(device).float().unsqueeze(1)
            opt.zero_grad(); loss=crit(model(x),y); loss.backward(); opt.step()
        model.eval(); preds=[]; trues=[]
        with torch.no_grad():
            for x,y in va:
                x=x.to(device); pred=model(x).squeeze(1).cpu().numpy(); preds.extend(pred); trues.extend(y.numpy())
        r2=r2_score(trues,preds)
    fold_r2.append(r2)
    if r2>best_r2:
        best_r2=r2; best_state={k:v.cpu().clone() for k,v in model.state_dict().items()}
    print(f'fold {fold} R2 {r2:.4f}')

print('mean cv R2', float(np.mean(fold_r2)), 'folds', fold_r2)
out=ROOT/'models/building_quality_augmented.pth'
if best_state: torch.save(best_state,out)
print('saved', out)
