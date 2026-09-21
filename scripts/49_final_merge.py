from pathlib import Path
from collections import defaultdict
import pandas as pd
from trueskill import Rating, rate_1vs1

ROOT=Path(r'D:\Codex\building_01')
orig=pd.read_csv(ROOT/'data/raw/comparison_results_20260921.csv')
fix1=pd.read_csv(ROOT/'data/raw/fix_comparison_results_20260921.csv')
fix2=pd.read_csv(ROOT/'data/raw/fix_comparison_results_pic002_20260921.csv')

bad_ids={"pic_122.jpg","pic_103.jpg","pic_012.jpg","pic_124.jpg","pic_146.jpg","pic_105.jpg","pic_002.jpg"}
orig_clean=orig[~(orig.left_id.isin(bad_ids)|orig.right_id.isin(bad_ids))].copy()
merged=pd.concat([orig_clean,fix1,fix2],ignore_index=True)
merged=merged.drop_duplicates(subset=["left_id","right_id","result"]).reset_index(drop=True)
merged.to_csv(ROOT/'data/processed/comparison_results_clean.csv',index=False,encoding='utf-8-sig')
print('orig',len(orig),'orig_clean',len(orig_clean),'fix1',len(fix1),'fix2',len(fix2),'merged',len(merged))

ratings=defaultdict(Rating)
for a,b,r in merged[['left_id','right_id','result']].itertuples(index=False):
    ra=ratings[a]; rb=ratings[b]
    if r=='left': ra,rb=rate_1vs1(ra,rb)
    elif r=='right': rb,ra=rate_1vs1(rb,ra)
    else: ra,rb=rate_1vs1(ra,rb,drawn=True)
    ratings[a]=ra; ratings[b]=rb

out=pd.DataFrame([{'pic_id':k,'trueskill.score':v.mu,'sigma':v.sigma} for k,v in ratings.items()]).sort_values('trueskill.score',ascending=False)
out.to_csv(ROOT/'data/processed/final_ratings.csv',index=False,encoding='utf-8-sig')
print(out.head(10).to_string(index=False))
print('saved final_ratings.csv')
