from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error
from pyproj import Transformer

ROOT = Path(r"D:\Codex\building_01")
df = pd.read_csv(ROOT / "data/processed/multiyear_lishi_with_district.csv")
transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
cx, cy = transformer.transform(114.305, 30.593)
df["center_dist"] = np.sqrt((df["centroid_x"] - cx)**2 + (df["centroid_y"] - cy)**2)
df = df.dropna(subset=["block_price", "building_score_mean", "center_dist"])
df = pd.get_dummies(df, columns=["year", "district"], prefix=["year", "district"], drop_first=True)
features = ["building_score_mean", "center_dist"] + [c for c in df.columns if c.startswith("year_") or c.startswith("district_")]
X = df[features].astype(float)
y = np.log(df["block_price"])
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)
model = RandomForestRegressor(n_estimators=300, random_state=42, n_jobs=-1).fit(Xtr, ytr)
pred = model.predict(Xte)
print("RF log R2 with district", r2_score(yte, pred), "RMSE", np.sqrt(mean_squared_error(yte, pred)))
