from pathlib import Path
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

ROOT=Path(r'D:\Codex\building_01')
scores=pd.read_csv(ROOT/'data/processed/building_quality_new_scores.csv')
feats=pd.read_csv(ROOT/'data/processed/feature_matrix.csv')
comm=pd.read_csv(ROOT/'data/processed/communities_geocoded.csv')
comm=comm[['community_id','lng','lat']].dropna()
comm=comm[comm.community_id.isin(scores.community_id)].merge(scores,on='community_id',how='inner')
comm['geometry']=[Point(x,y) for x,y in zip(comm.lng,comm.lat)]
comm_gdf=gpd.GeoDataFrame(comm,geometry='geometry',crs='EPSG:4326').to_crs('EPSG:3857')
blocks=gpd.read_file(ROOT/'data/processed/wuhan_blocks.gdb',layer='blocks').to_crs('EPSG:3857')[['block_id','geometry']]
joined=gpd.sjoin(comm_gdf,blocks,how='inner',predicate='within')
block_score=joined.groupby('block_id').agg(building_score_mean_new=('building_score_new','mean'), building_image_count_new=('building_score_new','size')).reset_index()

feats=feats.merge(block_score,on='block_id',how='left')
# 只替换有新评分的街区，其他保持原值
mask=feats['building_score_mean_new'].notna()
feats.loc[mask,'building_score_mean']=feats.loc[mask,'building_score_mean_new']
feats.loc[mask,'building_image_count']=feats.loc[mask,'building_image_count_new']
feats=feats.drop(columns=['building_score_mean_new','building_image_count_new'])
out=ROOT/'data/processed/feature_matrix_with_new_score.csv'
feats.to_csv(out,index=False,encoding='utf-8-sig')
print('updated blocks', int(mask.sum()), 'total blocks', len(feats))
print('saved', out)
