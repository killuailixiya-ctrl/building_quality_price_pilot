from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from pyproj import Transformer
import PyGRF

ROOT = Path(r"D:\Codex\building_01")
df = pd.read_csv(ROOT / "data/processed/multiyear_final_core.csv")

town_map = {
    "江岸区": "汉口", "江汉区": "汉口", "硚口区": "汉口",
    "武昌区": "武昌", "洪山区": "武昌", "青山区": "武昌",
    "汉阳区": "汉阳",
}
df["town"] = df["district"].map(town_map)
df = df.dropna(subset=["town", "block_price", "building_score_mean"])

transformer = Transformer.from_crs("EPSG:4326","EPSG:3857",always_xy=True)
cx,cy=transformer.transform(114.305,30.593)
df["center_dist"]=np.sqrt((df.centroid_x-cx)**2+(df.centroid_y-cy)**2)

poi_cols=[c for c in df.columns if c.endswith("_count") or c.endswith("_dist")]
base=["building_score_mean","center_dist","metro_dist_current"]+poi_cols
df=pd.get_dummies(df,columns=["year","town"],prefix=["year","town"],drop_first=True)
features=base+[c for c in df.columns if c.startswith("year_") or c.startswith("town_")]
features=list(dict.fromkeys([c for c in features if c in df.columns]))
X=df[features].replace([np.inf,-np.inf],np.nan).fillna(df[features].median())
y=np.log(df["block_price"])
coords=df[["centroid_x","centroid_y"]].to_numpy(dtype=float)

Xtr,Xte,ytr,yte,ctr,cte=train_test_split(X,y,coords,test_size=.2,random_state=42)
rf=RandomForestRegressor(n_estimators=300,random_state=42,n_jobs=-1).fit(Xtr,ytr)
pr=rf.predict(Xte)
print("RF", r2_score(yte,pr), np.sqrt(mean_squared_error(yte,pr)), mean_absolute_error(yte,pr))

bw=min(100,len(Xtr)-1)
grf=PyGRF.PyGRFBuilder(band_width=bw,n_estimators=30,max_features=0.3,n_jobs=-1,train_weighted=False,predict_weighted=False,resampled=False,random_state=42)
grf.fit(Xtr,ytr,pd.DataFrame(ctr,columns=["x","y"]))
preds=grf.predict(Xte,pd.DataFrame(cte,columns=["x","y"]),local_weight=0.5)
pg=np.array(preds[0])
print("GWRF", r2_score(yte,pg), np.sqrt(mean_squared_error(yte,pg)), mean_absolute_error(yte,pg))
print("samples", len(df), "years", df.filter(like='year_').shape[1])
