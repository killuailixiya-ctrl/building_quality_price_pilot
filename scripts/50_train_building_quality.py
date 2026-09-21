from __future__ import annotations
from pathlib import Path
import math
import pandas as pd
import numpy as np
import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, models
from PIL import Image
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score

ROOT = Path(r"D:\Codex\building_01")
ratings = pd.read_csv(ROOT / "data/processed/final_ratings.csv")
image_dir = ROOT / "apps/building_comparison_fix_pic002/images"
out_model = ROOT / "models/building_quality_shufflenet.pth"
out_model.parent.mkdir(parents=True, exist_ok=True)

transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225]),
])

class QualityDataset(Dataset):
    def __init__(self, df, root):
        self.df = df.reset_index(drop=True)
        self.root = Path(root)
    def __len__(self):
        return len(self.df)
    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        img = Image.open(self.root / row["pic_id"]).convert("RGB")
        return transform(img), float(row["trueskill.score"])

train_df, val_df = train_test_split(ratings, test_size=0.2, random_state=42)
train_ds = QualityDataset(train_df, image_dir)
val_ds = QualityDataset(val_df, image_dir)
train_loader = DataLoader(train_ds, batch_size=16, shuffle=True)
val_loader = DataLoader(val_ds, batch_size=16, shuffle=False)

try:
    model = models.shufflenet_v2_x1_0(weights=models.ShuffleNet_V2_X1_0_Weights.DEFAULT)
except Exception:
    model = models.shufflenet_v2_x1_0(weights=None)
model.fc = nn.Linear(model.fc.in_features, 1)
device = "cpu"
model = model.to(device)
criterion = nn.MSELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

epochs = 30
patience = 999
best_r2 = -float("inf")
best_epoch = 0
no_improve = 0
for epoch in range(1, epochs+1):
    model.train()
    for images, labels in train_loader:
        images, labels = images.to(device), labels.to(device).float().unsqueeze(1)
        optimizer.zero_grad()
        pred = model(images)
        loss = criterion(pred, labels)
        loss.backward()
        optimizer.step()
    model.eval()
    preds=[]; truths=[]
    with torch.no_grad():
        for images, labels in val_loader:
            images, labels = images.to(device), labels.to(device).float().unsqueeze(1)
            pred = model(images)
            preds.extend(pred.squeeze(1).cpu().numpy())
            truths.extend(labels.squeeze(1).cpu().numpy())
    r2 = r2_score(truths, preds)
    if r2 > best_r2:
        best_r2 = r2
        best_epoch = epoch
        no_improve = 0
        torch.save(model.state_dict(), out_model)
    else:
        no_improve += 1
    if epoch % 5 == 0 or epoch == epochs:
        print(f"epoch {epoch}/{epochs} val R2 {r2:.4f}")
    if no_improve >= patience:
        print(f"early stop at epoch {epoch}, no improvement for {patience} epochs")
        break

print("best val R2", best_r2)
print("saved", out_model)
