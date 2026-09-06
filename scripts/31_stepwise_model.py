from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error
from pyproj import Transformer

ROOT = Path(r"D:\Codex\building_01")
transformer = Transformer.from_crs("EPSG:4326","EPSG:3857",always_xy=True)
cx,cy=transformer.transform(114.305,30.593)

def run(name, path, include_poi=False, include_metro=False):
    df=pd.read_csv(path)
    df["center_dist"]=np.sqrt((df.centroid_x-cx)**2+(df.centroid_y-cy)**2)
    df=df.dropna(subset=["block_price","building_score_mean","center_dist"])
    base_feats=["building_score_mean","center_dist"]
    if include_poi:
        poi_cols=[c for c in df.columns if c.endswith("_count") or c.endswith("_dist")]
        poi_cols=[c for c in poi_cols if c in df.columns]
        base_feats += poi_cols
    if include_metro and "metro_dist_current" in df.columns:
        base_feats.append("metro_dist_current")
    df=pd.get_dummies(df,columns=["year","district"],prefix=["year","district"],drop_first=True)
    feats=base_feats+[c for c in df.columns if c.startswith("year_") or c.startswith("district_")]
    feats=list(dict.fromkeys(feats))
    X=df[feats].copy(); X=X.fillna(X.median())
    y=np.log(df["block_price"])
    Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=.2,random_state=42)
    m=RandomForestRegressor(n_estimators=300,random_state=42,n_jobs=-1).fit(Xtr,ytr)
    p=m.predict(Xte)
    print(name, "n", len(df), "R2", round(r2_score(yte,p),4), "RMSE", round(np.sqrt(mean_squared_error(yte,p)),4))

run("step0_baseline_district", ROOT/"data/processed/multiyear_lishi_with_district.csv", False, False)
run("step1_dynamic_poi", ROOT/"data/processed/multiyear_final_full.csv", True, False)
run("step2_metro_current", ROOT/"data/processed/multiyear_final_full.csv", True, True)
run("step3_core_only", ROOT/"data/processed/multiyear_final_core.csv", True, True)
