from pathlib import Path
import pandas as pd
import numpy as np
import arcpy
from pyproj import Transformer

ROOT = Path(r"D:\Codex\building_01")
df = pd.read_csv(ROOT / "data/processed/multiyear_final_core.csv")
transformer = Transformer.from_crs("EPSG:4326","EPSG:3857",always_xy=True)
cx,cy=transformer.transform(114.305,30.593)
df["center_dist"]=np.sqrt((df.centroid_x-cx)**2+(df.centroid_y-cy)**2)
df=df.dropna(subset=["block_price","building_score_mean","center_dist"])
poi_cols=[c for c in df.columns if c.endswith("_count") or c.endswith("_dist")]
base=["building_score_mean","center_dist","metro_dist_current"]+poi_cols
df=pd.get_dummies(df,columns=["year","district"],prefix=["year","district"],drop_first=True)
features=base+[c for c in df.columns if c.startswith("year_") or c.startswith("district_")]
features=list(dict.fromkeys([c for c in features if c in df.columns]))
df=df[["block_id","block_price","centroid_x","centroid_y"]+features].copy().fillna(0)
features=[f for f in features if df[f].std() > 1e-8]

arcpy.env.overwriteOutput=True
gdb=str(ROOT/"data/processed/multiyear_gwr.gdb")
if not arcpy.Exists(gdb):
    arcpy.management.CreateFileGDB(str(ROOT/"data/processed"),"multiyear_gwr.gdb")
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
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
print("GWR",r2_score(y,p),np.sqrt(mean_squared_error(y,p)),mean_absolute_error(y,p))
