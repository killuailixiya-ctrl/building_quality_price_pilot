from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from pyproj import Transformer
import statsmodels.api as sm

ROOT = Path(r"D:\Codex\building_01")
df = pd.read_csv(ROOT / "data/processed/multiyear_feature_matrix.csv")
transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
cx, cy = transformer.transform(114.305, 30.593)
df["center_dist"] = np.sqrt((df["centroid_x"] - cx)**2 + (df["centroid_y"] - cy)**2)
df = df.dropna(subset=["block_price", "building_score_mean"])
features = ["building_score_mean", "building_image_count", "center_dist"]
for col in features:
    df[col] = pd.to_numeric(df[col], errors="coerce")
df = df.dropna(subset=features)
df = pd.get_dummies(df, columns=["year"], prefix="year", drop_first=True)
year_cols = [c for c in df.columns if c.startswith("year_")]
X = df[features + year_cols].astype(float)
y = np.log(df["block_price"])
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)
rf = RandomForestRegressor(n_estimators=300, random_state=42, n_jobs=-1).fit(Xtr, ytr)
p = rf.predict(Xte)
print("RF log R2", r2_score(yte, p), "RMSE", np.sqrt(mean_squared_error(yte, p)))
ols = sm.OLS(ytr, sm.add_constant(Xtr)).fit()
po = ols.predict(sm.add_constant(Xte))
print("OLS log R2", r2_score(yte, po), "RMSE", np.sqrt(mean_squared_error(yte, po)))
pd.Series(ols.params, index=["const"] + list(X.columns)).to_csv(ROOT / "reports/multiyear_ols_coefs.csv", encoding="utf-8-sig")
print(df.groupby("year").size() if False else "done")
