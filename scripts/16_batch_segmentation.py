from __future__ import annotations
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, r"E:\刘天辰\CSAILVion")

import pandas as pd
import torch
from PIL import Image
from torchvision import transforms
from mit_semseg.models import ModelBuilder, SegmentationModule
from src.wuhan_pilot.image_quality import IMAGE_SUFFIXES
from src.wuhan_pilot import config

ROOT = Path(r"E:\刘天辰\CSAILVion")
ENC = ROOT / "ckpt/ade20k-resnet50dilated-ppm_deepsup/encoder_epoch_20.pth"
DEC = ROOT / "ckpt/ade20k-resnet50dilated-ppm_deepsup/decoder_epoch_20.pth"
BUILDING_CLASSES = {2, 26, 49, 85}
SIZE = 160
# 当前强制 CPU，避免 CUDA 内核与旧模型不兼容。
transform = transforms.Compose([
    transforms.Resize((SIZE, SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-communities", type=int, default=1000)
    parser.add_argument("--max-per-community", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=8)
    args = parser.parse_args()

    enc = ModelBuilder.build_encoder(arch="resnet50dilated", fc_dim=2048, weights=str(ENC))
    dec = ModelBuilder.build_decoder(arch="ppm_deepsup", fc_dim=2048, num_class=150, weights=str(DEC), use_softmax=True)
    device = "cpu"
    model = SegmentationModule(enc, dec, torch.nn.NLLLoss(ignore_index=-1)).to(device).eval()

    geocoded = pd.read_csv(config.DATA_PROCESSED / "communities_geocoded.csv")
    geocoded = geocoded[(geocoded["lng"].notna()) & (geocoded["lat"].notna())].copy()
    if args.max_communities:
        geocoded = geocoded.head(args.max_communities)

    paths = []
    for community_id in geocoded["community_id"].astype(int).tolist():
        directory = config.COMMUNITY_IMAGES_ROOT / str(community_id)
        if not directory.is_dir():
            continue
        files = [child for child in directory.iterdir() if child.is_file() and child.suffix.lower() in IMAGE_SUFFIXES]
        for path in files[:args.max_per_community]:
            paths.append((int(community_id), path))

    rows = []
    batch_meta = []
    batch_tensors = []
    def flush():
        if not batch_tensors:
            return
        tensor = torch.stack(batch_tensors).to(device)
        with torch.no_grad():
            scores = model({"img_data": tensor}, segSize=(SIZE, SIZE))
            _, preds = torch.max(scores, dim=1)
        preds = preds.numpy()
        for (community_id, path), pred in zip(batch_meta, preds):
            ratio = float(sum((pred == c).sum() for c in BUILDING_CLASSES) / pred.size)
            rows.append({"community_id": community_id, "filename": path.name, "building_ratio": ratio, "is_building_likely": int(ratio >= 0.08)})
        batch_meta.clear()
        batch_tensors.clear()

    for community_id, path in paths:
        try:
            tensor = transform(Image.open(path).convert("RGB"))
            batch_meta.append((community_id, path))
            batch_tensors.append(tensor)
            if len(batch_tensors) >= args.batch_size:
                flush()
        except Exception as exc:
            print("skip", path, exc)
    flush()

    out = config.IMAGES_DIR / "image_building_segmentation.csv"
    pd.DataFrame(rows).to_csv(out, index=False, encoding="utf-8-sig")
    print("rows:", len(rows))
    print("building_likely:", int(pd.DataFrame(rows)["is_building_likely"].sum()) if rows else 0)
    print("written:", out)

if __name__ == "__main__":
    main()



