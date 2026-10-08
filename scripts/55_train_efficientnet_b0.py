from pathlib import Path
import pandas as pd
import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, models
from PIL import Image
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score

ROOT=Path(r'D:\Codex\building_01')
ratings=pd.read_csv(ROOT/'data/processed/final_ratings.csv')
img_dir=ROOT/'apps/building_comparison_fix_pic002/images'

train_transform=transforms.Compose([
    transforms.RandomResizedCrop(224, scale=(0.75,1.0)),
    transforms.RandomHorizontalFlip(),
    transforms.ColorJitter(brightness=0.2, contrast=0.2),
    transforms.ToTensor(), transforms.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225]),
])
val_transform=transforms.Compose([
    transforms.Resize(256), transforms.CenterCrop(224), transforms.ToTensor(),
    transforms.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225]),
])

class DS(Dataset):
    def __init__(self,df,root,transform):
        self.df=df.reset_index(drop=True); self.root=Path(root); self.transform=transform
    def __len__(self): return len(self.df)
    def __getitem__(self,i):
        row=self.df.iloc[i]; img=Image.open(self.root/row['pic_id']).convert('RGB')
        return self.transform(img), float(row['trueskill.score'])

try:
    model=models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.DEFAULT)
except Exception:
    model=torch.load(r"G:\huanghaojun_buliding\08街景主观感知\model_results_20250924_104638_质量_EfficientNet_300_200\best_model_质量.pth", map_location='cpu', weights_only=False)
model.classifier=nn.Sequential(nn.Dropout(0.2), nn.Linear(1280,1))
for p in model.features.parameters(): p.requires_grad=False
model.classifier[1].requires_grad=True

tr_df,va_df=train_test_split(ratings,test_size=0.2,random_state=42)
tr=DataLoader(DS(tr_df,img_dir,train_transform),batch_size=16,shuffle=True)
va=DataLoader(DS(va_df,img_dir,val_transform),batch_size=16)
opt=torch.optim.Adam(model.classifier.parameters(),lr=1e-3)
crit=nn.MSELoss()
best_r2=-999; best_state=None; patience=8; no_improve=0
for epoch in range(1,51):
    model.train()
    for x,y in tr:
        x=x; y=y.float().unsqueeze(1)
        opt.zero_grad(); loss=crit(model(x),y); loss.backward(); opt.step()
    model.eval(); preds=[]; truths=[]
    with torch.no_grad():
        for x,y in va:
            preds.extend(model(x).squeeze(1).numpy()); truths.extend(y.numpy())
    r2=r2_score(truths,preds)
    if r2>best_r2:
        best_r2=r2; best_state={k:v.clone() for k,v in model.state_dict().items()}; no_improve=0
    else: no_improve+=1
    if epoch%5==0: print(epoch,r2)
    if no_improve>=patience: break
out=ROOT/'models/building_quality_efficientnet.pth'
if best_state: torch.save(best_state,out)
print('best R2',best_r2,'saved',out)
