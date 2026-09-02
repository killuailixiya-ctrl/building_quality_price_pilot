"""建筑图像质量代理分。

预实验默认使用无需 GPU 的图像统计代理；有 PyTorch/CLIP 环境时可切换为嵌入代理。
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from PIL import Image, ImageFilter, ImageStat

from . import config
from .utils import ensure_dir, write_json


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def image_statistics(path: Path) -> dict[str, float]:
    with Image.open(path) as image:
        image = image.convert("RGB")
        gray = image.convert("L")
        edges = gray.filter(ImageFilter.FIND_EDGES)
        edge_stat = ImageStat.Stat(edges)
        rgb_stat = ImageStat.Stat(image)
        width, height = image.size

        r_mean, g_mean, b_mean = rgb_stat.mean
        r_var, g_var, b_var = rgb_stat.var
        brightness = 0.299 * r_mean + 0.587 * g_mean + 0.114 * b_mean
        colorfulness = (r_var + g_var + b_var) ** 0.5
        sharpness = edge_stat.mean[0]

        return {
            "width": float(width),
            "height": float(height),
            "aspect_ratio": round(width / height, 6),
            "brightness": round(brightness, 4),
            "colorfulness": round(colorfulness, 4),
            "sharpness": round(sharpness, 4),
        }


def heuristic_score(stats: dict[str, float]) -> float:
    aspect_penalty = min(1.0, abs(stats["aspect_ratio"] - 1.0) / 1.5)
    brightness_score = 1.0 - abs(stats["brightness"] - 128.0) / 128.0
    normalized_color = min(1.0, stats["colorfulness"] / 100.0)
    normalized_sharpness = min(1.0, stats["sharpness"] / 80.0)
    score = (
        0.25 * (1.0 - aspect_penalty)
        + 0.25 * brightness_score
        + 0.25 * normalized_color
        + 0.25 * normalized_sharpness
    )
    return round(100 * score, 4)


def iter_images(community_match_csv: Path, max_communities: int | None = None, max_per_community: int = 6):
    frame = pd.read_csv(community_match_csv)
    frame = frame[frame["image_dir_exists"].fillna(False)].copy()
    if max_communities:
        frame = frame.head(max_communities)
    for _, row in frame.iterrows():
        directory = Path(config.COMMUNITY_IMAGES_ROOT) / str(row["community_id"])
        if not directory.is_dir():
            continue
        files = [
            child
            for child in directory.iterdir()
            if child.is_file() and child.suffix.lower() in IMAGE_SUFFIXES
        ]
        for path in files[:max_per_community]:
            yield int(row["community_id"]), path


def run_image_proxy(
    community_match_csv: Path | None = None,
    output_dir: Path | None = None,
    max_communities: int | None = None,
    max_per_community: int = 6,
) -> Path:
    community_match_csv = Path(community_match_csv or (config.DATA_PROCESSED / config.OUTPUT_COMMUNITY_MATCH.name))
    output_dir = output_dir or config.IMAGES_DIR
    ensure_dir(output_dir)

    rows = []
    for community_id, path in iter_images(
        community_match_csv,
        max_communities=max_communities,
        max_per_community=max_per_community,
    ):
        try:
            stats = image_statistics(path)
            stats["community_id"] = community_id
            stats["filename"] = path.name
            stats["quality_proxy"] = heuristic_score(stats)
            rows.append(stats)
        except OSError:
            continue

    result = pd.DataFrame(rows)
    out_path = output_dir / "image_proxy_scores.csv"
    result.to_csv(out_path, index=False, encoding="utf-8-sig")

    summary = {
        "image_rows": int(len(result)),
        "community_rows": int(result["community_id"].nunique()) if len(result) else 0,
        "quality_proxy_mean": float(result["quality_proxy"].mean()) if len(result) else None,
        "quality_proxy_std": float(result["quality_proxy"].std()) if len(result) else None,
        "output": str(out_path),
    }
    write_json(output_dir / "image_proxy_summary.json", summary)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--community-match", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--max-communities", type=int, default=None)
    parser.add_argument("--max-per-community", type=int, default=6)
    args = parser.parse_args()
    run_image_proxy(
        community_match_csv=args.community_match,
        output_dir=args.output_dir,
        max_communities=args.max_communities,
        max_per_community=args.max_per_community,
    )


if __name__ == "__main__":
    main()
