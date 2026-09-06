"""盘点预实验依赖的关键数据是否存在，并生成原始数据登记表。"""

from __future__ import annotations

import hashlib
from pathlib import Path

from . import config
from .utils import ensure_dir, write_json


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def inventory_key_files() -> list[dict[str, str | int | None]]:
    paths = [
        ("anjuke_2022_csv", config.ANJUKE_CSV),
        ("community_images_root", config.COMMUNITY_IMAGES_ROOT),
        ("road_network", config.ROAD_NETWORK),
        ("research_area", config.RESEARCH_AREA),
        ("poi_2021_csv", config.POI_2021_CSV),
        ("poi_2023_dir", config.POI_2023_DIR),
        ("metro_dir", config.METRO_DIR),
        ("ndvi_dir", config.NDVI_DIR),
        ("landcover_dir", config.LANDCOVER_DIR),
        ("admin_dir", config.ADMIN_DIR),
        ("gis_base_dir", config.GIS_BASE_DIR),
        ("historical_city_prices", config.HISTORICAL_CITY_PRICES),
    ]
    rows = []
    for key, raw_path in paths:
        path = Path(raw_path)
        size: int | None = None
        if path.is_file():
            size = path.stat().st_size
        rows.append(
            {
                "key": key,
                "path": str(path),
                "exists": path.exists(),
                "kind": "file" if path.is_file() else ("dir" if path.is_dir() else "missing"),
                "size_bytes": size,
            }
        )
    return rows


def inventory_community_images(max_dirs: int | None = None) -> dict[str, int]:
    root = Path(config.COMMUNITY_IMAGES_ROOT)
    if not root.is_dir():
        return {"community_dirs": 0, "image_files": 0}
    dirs = [p for p in root.iterdir() if p.is_dir()]
    if max_dirs:
        dirs = dirs[:max_dirs]
    image_count = 0
    for directory in dirs:
        try:
            image_count += sum(
                1
                for child in directory.iterdir()
                if child.is_file() and child.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
            )
        except OSError:
            continue
    return {
        "sampled_community_dirs": len(dirs),
        "sampled_image_files": image_count,
    }


def run_inventory(output_dir: Path | None = None) -> Path:
    output_dir = output_dir or config.DATA_RAW
    ensure_dir(output_dir)
    rows = inventory_key_files()
    image_stats = inventory_community_images(max_dirs=50)
    payload = {
        "key_files": rows,
        "community_images_sample": image_stats,
    }
    out = output_dir / "raw_data_inventory.json"
    write_json(out, payload)
    return out


if __name__ == "__main__":
    result = run_inventory()
    print(f"written: {result}")

