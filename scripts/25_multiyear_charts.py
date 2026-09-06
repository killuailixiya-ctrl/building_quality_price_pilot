from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(r"D:\Codex\building_01")
df = pd.read_csv(ROOT / "data/processed/multiyear_feature_matrix.csv")
plt.figure(figsize=(8, 5))
df.boxplot(column="block_price", by="year")
plt.title("Block price distribution by year")
plt.suptitle("")
plt.xlabel("Year")
plt.ylabel("Block price")
plt.tight_layout()
plt.savefig(ROOT / "reports/multiyear_price_boxplot.png", dpi=300)
print("saved", ROOT / "reports/multiyear_price_boxplot.png")
