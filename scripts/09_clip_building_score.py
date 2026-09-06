from __future__ import annotations
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import clip
import pandas as pd
import torch
from PIL import Image

from src.wuhan_pilot.image_quality import iter_images
from src.wuhan_pilot import config

PROMPTS_HIGH = [
    "a high-quality well-maintained modern residential building facade",
    "a clean beautiful residential building exterior",
]
PROMPTS_LOW = [
    "an old dilapidated low-quality residential building facade",
    "a shabby dirty residential building exterior",
]

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-communities", type=int, default=100)
    parser.add_argument("--max-per-community", type=int, default=6)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else args.device
    model, preprocess = clip.load("ViT-B/32", device=device)
    model.eval()
    high = clip.tokenize(PROMPTS_HIGH).to(device)
    low = clip.tokenize(PROMPTS_LOW).to(device)

    rows = []
    match_csv = config.DATA_PROCESSED / config.OUTPUT_COMMUNITY_MATCH.name
    for community_id, path in iter_images(match_csv, max_communities=args.max_communities, max_per_community=args.max_per_community):
        try:
            image = preprocess(Image.open(path).convert("RGB")).unsqueeze(0).to(device)
            with torch.no_grad():
                image_features = model.encode_image(image)
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                high_features = model.encode_text(high)
                high_features = high_features / high_features.norm(dim=-1, keepdim=True)
                low_features = model.encode_text(low)
                low_features = low_features / low_features.norm(dim=-1, keepdim=True)
                high_sim = float((image_features @ high_features.T).mean())
                low_sim = float((image_features @ low_features.T).mean())
            score = 100 * (high_sim - low_sim + 1) / 2
            rows.append({"community_id": community_id, "filename": path.name, "clip_quality": score, "high_sim": high_sim, "low_sim": low_sim})
        except Exception as exc:
            print("skip", path, exc)

    out = config.IMAGES_DIR / "image_clip_scores.csv"
    pd.DataFrame(rows).to_csv(out, index=False, encoding="utf-8-sig")
    print("rows:", len(rows))
    print("written:", out)

if __name__ == "__main__":
    main()

