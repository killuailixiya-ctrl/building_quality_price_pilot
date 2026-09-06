from pathlib import Path
import pandas as pd
import numpy as np
import shap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import PartialDependenceDisplay
from pyproj import Transformer

ROOT = Path(r"D:\Codex\building_01")
df = pd.read_csv(ROOT / "data/processed/multiyear_final_core.csv")
town_map = {"江岸区":"汉口","江汉区":"汉口","硚口区":"汉口","武昌区":"武昌","洪山区":"武昌","青山区":"武昌","汉阳区":"汉阳"}
df["town"] = df["district"].map(town_map)
df = df.dropna(subset=["town","block_price","building_score_mean"])
transformer = Transformer.from_crs("EPSG:4326","EPSG:3857",always_xy=True)
cx,cy = transformer.transform(114.305,30.593)
df["center_dist"] = np.sqrt((df.centroid_x-cx)**2+(df.centroid_y-cy)**2)

poi_cols=[c for c in df.columns if c.endswith("_count") or c.endswith("_dist")]
base=["building_score_mean","center_dist","metro_dist_current"]+poi_cols
df=pd.get_dummies(df,columns=["year","town"],prefix=["year","town"],drop_first=True)
features=base+[c for c in df.columns if c.startswith("year_") or c.startswith("town_")]
features=list(dict.fromkeys([c for c in features if c in df.columns]))
X=df[features].replace([np.inf,-np.inf],np.nan).fillna(df[features].median())
y=np.log(df["block_price"])

model=RandomForestRegressor(n_estimators=100,random_state=42,n_jobs=-1).fit(X,y)
explainer=shap.TreeExplainer(model)
X_sample=X.sample(500,random_state=42).astype(float)
sv=explainer.shap_values(X_sample)
imp=pd.Series(np.abs(sv).mean(0),index=features).sort_values(ascending=False)
imp.to_csv(ROOT/"reports/three_town_shap_importance.csv",index_label="feature")

top=imp.head(5).index.tolist()
fig,ax=plt.subplots(figsize=(10,7))
PartialDependenceDisplay.from_estimator(model,X,top,ax=ax,grid_resolution=25)
fig.savefig(ROOT/"reports/three_town_pdp_top5.png",dpi=300,bbox_inches="tight")
plt.close(fig)

print(imp.head(15).to_string())
print("saved SHAP and PDP")
