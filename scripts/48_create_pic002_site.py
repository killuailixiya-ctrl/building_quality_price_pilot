from pathlib import Path
import shutil, json
import pandas as pd

ROOT=Path(r'D:\Codex\building_01')
src=ROOT/'apps/building_comparison_fix'
dst=ROOT/'apps/building_comparison_fix_pic002'
if dst.exists(): shutil.rmtree(dst)
shutil.copytree(src, dst)

fix=pd.read_csv(ROOT/'data/raw/fix_comparison_results_20260921.csv')
fix_pairs=set(tuple(sorted((a,b))) for a,b in fix[['left_id','right_id']].itertuples(index=False))
orig=pd.read_csv(ROOT/'data/raw/comparison_results_20260921.csv')
all_ids=sorted(set(orig.left_id).union(orig.right_id))
pairs=[]
for x in all_ids:
    if x=='pic_002.jpg': continue
    p=tuple(sorted(('pic_002.jpg',x)))
    if p not in fix_pairs:
        pairs.append(p)
pairs=sorted(pairs)
(dst/'fix_pairs.json').write_text(json.dumps([[a,b] for a,b in pairs], ensure_ascii=False), encoding='utf-8')
print('new site pairs', len(pairs))
