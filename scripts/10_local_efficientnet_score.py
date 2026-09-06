from __future__ import annotations
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import torch
from PIL import Image
from torchvision import transforms

from src.wuhan_pilot.image_quality import IMAGE_SUFFIXES
from src.wuhan_pilot import config

# 本地 EfficientNet 质量模型路径。
MODEL_PATH = Path(r"G:\huanghaojun_buliding\08街景主观感知\model_results_20250924_104638_质量_EfficientNet_300_200\best_model_质量.pth")

# 与模型训练时一致的预处理。
transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-communities", type=int, default=100)
    parser.add_argument("--max-per-community", type=int, default=6)
    args = parser.parse_args()

    model = torch.load(MODEL_PATH, map_location="cpu", weights_only=False)
    model.eval()
    rows = []
    geocoded = pd.read_csv(config.DATA_PROCESSED / "communities_geocoded.csv")
    geocoded = geocoded[(geocoded["lng"].notna()) & (geocoded["lat"].notna())].copy()
    if args.max_communities:
        geocoded = geocoded.head(args.max_communities)

    for community_id in geocoded["community_id"].astype(int).tolist():
        directory = config.COMMUNITY_IMAGES_ROOT / str(community_id)
        if not directory.is_dir():
            continue
        files = [child for child in directory.iterdir() if child.is_file() and child.suffix.lower() in IMAGE_SUFFIXES]
        for path in files[:args.max_per_community]:
            try:
                image = transform(Image.open(path).convert("RGB")).unsqueeze(0)
                with torch.no_grad():
                    score = float(model(image).squeeze().item())
                rows.append({"community_id": community_id, "filename": path.name, "efficientnet_quality": score})
            except Exception as exc:
                print("skip", path, exc)

    out = config.IMAGES_DIR / "image_efficientnet_scores.csv"
    pd.DataFrame(rows).to_csv(out, index=False, encoding="utf-8-sig")
    print("rows:", len(rows))
    print("written:", out)

if __name__ == "__main__":
    main()

