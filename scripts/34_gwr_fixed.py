from pathlib import Path
import pandas as pd
import numpy as np
import arcpy
from pyproj import Transformer
from statsmodels.stats.outliers_influence import variance_inflation_factor
import statsmodels.api as sm
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

ROOT = Path(r"D:\Codex\building_01")
df = pd.read_csv(ROOT / "data/processed/multiyear_final_core.csv")
transformer = Transformer.from_crs("EPSG:4326","EPSG:3857",always_xy=True)
cx,cy=transformer.transform(114.305,30.593)
df["center_dist"]=np.sqrt((df.centroid_x-cx)**2+(df.centroid_y-cy)**2)
df=df.dropna(subset=["block_price","building_score_mean","center_dist"])

candidates=["building_score_mean","center_dist","metro_dist_current"]+[c for c in df.columns if c.endswith("_dist")]
candidates=[c for c in candidates if c in df.columns]
# 去掉零方差字段
candidates=[c for c in candidates if df[c].std() > 1e-8]
# VIF 逐步剔除
kept=candidates[:]
while True:
    X=df[kept].fillna(df[kept].median())
    Xk=sm.add_constant(X)
    vif=pd.Series([variance_inflation_factor(Xk.values,i) for i in range(1,Xk.shape[1])], index=Xk.columns[1:])
    if vif.max() <= 5:
        break
    kept.remove(vif.idxmax())
features=["center_dist","metro_dist_current","building_score_mean","kindergarten_dist","park_dist"]
print("features", features)

df=df[["block_id","block_price","centroid_x","centroid_y"]+features].copy()
df=df.fillna(df.median(numeric_only=True))

arcpy.env.overwriteOutput=True
gdb=str(ROOT/"data/processed/gwr_fixed.gdb")
if not arcpy.Exists(gdb):
    arcpy.management.CreateFileGDB(str(ROOT/"data/processed"),"gwr_fixed.gdb")
fc=gdb+"\\points"
if arcpy.Exists(fc): arcpy.management.Delete(fc)
arcpy.management.CreateFeatureclass(gdb,"points","POINT",spatial_reference=arcpy.SpatialReference(3857))
arcpy.management.AddField(fc,"block_id","TEXT",field_length=32)
arcpy.management.AddField(fc,"block_price","DOUBLE")
for f in features:
    arcpy.management.AddField(fc,f,"DOUBLE")
fields=["SHAPE@","block_id","block_price"]+features
with arcpy.da.InsertCursor(fc,fields) as cur:
    for _,row in df.iterrows():
        p=arcpy.Point(float(row["centroid_x"]),float(row["centroid_y"]))
        vals=[p,str(row["block_id"]),float(row["block_price"])]+[float(row[f]) for f in features]
        cur.insertRow(vals)
out=gdb+"\\gwr_out"
arcpy.stats.GWR(in_features=fc,dependent_variable="block_price",model_type="CONTINUOUS",explanatory_variables=features,output_features=out,neighborhood_type="NUMBER_OF_NEIGHBORS",neighborhood_selection_method="USER_DEFINED",number_of_neighbors=100,local_weighting_scheme="GAUSSIAN")
rows=[r for r in arcpy.da.SearchCursor(out,["block_price","PREDICTED"])]
y=np.array([r[0] for r in rows]); p=np.array([r[1] for r in rows])
metrics={"model":"GWR","r2":r2_score(y,p),"rmse":np.sqrt(mean_squared_error(y,p)),"mae":mean_absolute_error(y,p)}
print(metrics)
pd.DataFrame([metrics]).to_csv(ROOT/"reports/gwr_fixed_metrics.csv",index=False,encoding="utf-8-sig")
