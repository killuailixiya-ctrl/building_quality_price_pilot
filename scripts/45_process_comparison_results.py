from pathlib import Path
from collections import defaultdict
import pandas as pd
from trueskill import Rating, rate_1vs1

ROOT = Path(r"D:\Codex\building_01")
df = pd.read_csv(ROOT / "data/raw/comparison_results_20260921.csv")
print("raw rows", len(df))
# 去除完全相同重复行
df = df.drop_duplicates(subset=["left_id", "right_id", "result"]).copy()
print("unique rows", len(df))

bad = ["pic_122.jpg","pic_103.jpg","pic_012.jpg","pic_124.jpg","pic_146.jpg","pic_105.jpg"]
mask = df["left_id"].isin(bad) | df["right_id"].isin(bad)
bad_rows = int(mask.sum())
bad_pairs = set()
for a,b in df.loc[mask, ["left_id","right_id"]].itertuples(index=False):
    bad_pairs.add(tuple(sorted((a,b))))
print("rows involving bad", bad_rows)
print("unique pairs involving bad", len(bad_pairs))

ratings = defaultdict(Rating)
for a,b,r in df[["left_id","right_id","result"]].itertuples(index=False):
    ra = ratings[a]; rb = ratings[b]
    if r == "left":
        ra, rb = rate_1vs1(ra, rb)
    elif r == "right":
        rb, ra = rate_1vs1(rb, ra)
    else:
        ra, rb = rate_1vs1(ra, rb, drawn=True)
    ratings[a] = ra; ratings[b] = rb

out = pd.DataFrame([
    {"pic_id": k, "trueskill.score": v.mu, "sigma": v.sigma}
    for k,v in ratings.items()
]).sort_values("trueskill.score", ascending=False)
out.to_csv(ROOT / "data/processed/final_ratings.csv", index=False, encoding="utf-8-sig")
print(out.head(10).to_string(index=False))
print("saved final_ratings.csv")
