from pathlib import Path
import pandas as pd
import numpy as np
import torch
from torchvision import transforms, models
from PIL import Image
from sklearn.model_selection import cross_val_predict, KFold
from sklearn.linear_model import RidgeCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

ROOT=Path(r'D:\Codex\building_01')
ratings=pd.read_csv(ROOT/'data/processed/final_ratings.csv')
img_dir=ROOT/'apps/building_comparison_fix_pic002/images'

transform=transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225]),
])

model=torch.load(r"G:\huanghaojun_buliding\08街景主观感知\model_results_20250924_104638_质量_EfficientNet_300_200\best_model_质量.pth", map_location="cpu", weights_only=False)
model.classifier=torch.nn.Identity()
model.eval()

features=[]; labels=[]
for _,row in ratings.iterrows():
    img=Image.open(img_dir/row['pic_id']).convert('RGB')
    x=transform(img).unsqueeze(0)
    with torch.no_grad():
        feat=model(x).squeeze(0).numpy()
    features.append(feat); labels.append(float(row['trueskill.score']))
X=np.array(features); y=np.array(labels)

kf=KFold(n_splits=5, shuffle=True, random_state=42)
ridge=RidgeCV(alphas=np.logspace(-3,3,20))
pred=cross_val_predict(ridge,X,y,cv=kf)
print('Ridge CV R2',r2_score(y,pred),'RMSE',np.sqrt(mean_squared_error(y,pred)),'MAE',mean_absolute_error(y,pred))

rf=RandomForestRegressor(n_estimators=300,random_state=42,n_jobs=-1)
pred_rf=cross_val_predict(rf,X,y,cv=kf)
print('RF CV R2',r2_score(y,pred_rf),'RMSE',np.sqrt(mean_squared_error(y,pred_rf)),'MAE',mean_absolute_error(y,pred_rf))
