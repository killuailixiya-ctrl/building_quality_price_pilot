from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(r"D:\Codex\building_01")
metrics = json.loads((ROOT / "reports/final_model_metrics.json").read_text(encoding="utf-8"))
model_metrics = {k: v for k, v in metrics.items() if "r2" in v and isinstance(v["r2"], (int, float))}
plt.figure(figsize=(8, 5))
names = list(model_metrics)
r2 = [model_metrics[k]["r2"] for k in names]
plt.bar(names, r2, color=["#7f8c8d", "#e67e22", "#2980b9", "#27ae60"])
plt.ylabel("R²")
plt.title("Model comparison")
for i, v in enumerate(r2):
    plt.text(i, v + 0.005, f"{v:.3f}", ha="center")
plt.tight_layout()
plt.savefig(ROOT / "reports/model_comparison.png", dpi=300)
plt.close()

df = pd.read_csv(ROOT / "data/processed/feature_matrix.csv").dropna(subset=["block_price"])
plt.figure(figsize=(9, 7))
sc = plt.scatter(df["centroid_x"], df["centroid_y"], c=df["block_price"], cmap="viridis", s=8, alpha=0.7)
plt.colorbar(sc, label="block_price")
plt.title("Wuhan block price spatial distribution")
plt.axis("equal")
plt.tight_layout()
plt.savefig(ROOT / "reports/price_spatial.png", dpi=300)
plt.close()

print("saved model_comparison.png and price_spatial.png")
