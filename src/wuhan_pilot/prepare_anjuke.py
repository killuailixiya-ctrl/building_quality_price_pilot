"""清洗安居客武汉 2022 数据，匹配建筑照片目录。"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from . import config
from .utils import ensure_dir, parse_numeric, write_json


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def count_images(community_dir: Path) -> int:
    if not community_dir.is_dir():
        return 0
    return sum(
        1
        for child in community_dir.iterdir()
        if child.is_file() and child.suffix.lower() in IMAGE_SUFFIXES
    )


def clean_anjuke(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    # 把字符串价格解析成数值，并剔除“暂无”等无效值。
    out["price_yuan_m2"] = out["price"].map(parse_numeric)
    out = out[out["price_yuan_m2"].notna()].copy()
    # 只保留合理价格区间，避免异常值干扰。
    out = out[(out["price_yuan_m2"] > 1000) & (out["price_yuan_m2"] < 200000)].copy()

    # community_id 必须能转成整数，否则无法和照片目录对应。
    out["community_id"] = pd.to_numeric(out["community_id"], errors="coerce")
    out = out[out["community_id"].notna()].copy()
    out["community_id"] = out["community_id"].astype(int)

    out["floor_area_ratio"] = out.get("容积率", pd.Series(dtype=float)).map(parse_numeric)
    out["property_fee"] = out.get("物业费", pd.Series(dtype=float)).map(parse_numeric)
    out["green_rate"] = out.get("绿化率", pd.Series(dtype=float)).map(
        lambda x: parse_numeric(str(x).replace("%", "")) if pd.notna(x) else None
    )

    # 从“竣工时间”中提取年份，再计算房龄。
    completion = out.get("竣工时间", pd.Series(dtype=str)).astype(str)
    year = completion.str.extract(r"(19\d{2}|20\d{2})", expand=False)
    out["completion_year"] = pd.to_numeric(year, errors="coerce")
    out["age_years"] = config.YEAR - out["completion_year"]

    columns = [
        "community_id",
        "community",
        "area",
        "s_area",
        "price",
        "price_yuan_m2",
        "floor_area_ratio",
        "property_fee",
        "green_rate",
        "completion_year",
        "age_years",
        "小区地址",
        "物业公司",
        "物业类型",
        "建筑类型",
    ]
    columns = [col for col in columns if col in out.columns]
    return out[columns].drop_duplicates(subset=["community_id"]).reset_index(drop=True)


def match_images(df: pd.DataFrame, image_root: Path, count_files: bool) -> pd.DataFrame:
    image_root = Path(image_root)
    matched = []
    for community_id in df["community_id"].tolist():
        community_dir = image_root / str(community_id)
        # 图片目录名就是 community_id。
        exists = community_dir.is_dir()
        image_count = count_images(community_dir) if (exists and count_files) else None
        matched.append(
            {
                "community_id": community_id,
                "image_dir_exists": exists,
                "image_count": image_count,
            }
        )
    match_df = pd.DataFrame(matched)
    return df.merge(match_df, on="community_id", how="left")


def run_prepare(
    csv_path: Path | None = None,
    image_root: Path | None = None,
    output_dir: Path | None = None,
    count_files: bool = False,
    limit: int | None = None,
) -> dict[str, Path]:
    csv_path = Path(csv_path or config.ANJUKE_CSV)
    image_root = Path(image_root or config.COMMUNITY_IMAGES_ROOT)
    output_dir = output_dir or config.DATA_PROCESSED
    ensure_dir(output_dir)

    raw = pd.read_csv(csv_path, dtype={"community_id": str})
    if limit:
        raw = raw.head(limit)
    cleaned = clean_anjuke(raw)
    matched = match_images(cleaned, image_root, count_files=count_files)

    clean_path = output_dir / config.OUTPUT_ANJUKE_CLEAN.name
    match_path = output_dir / config.OUTPUT_COMMUNITY_MATCH.name
    matched.to_csv(clean_path, index=False, encoding="utf-8-sig")
    matched.to_csv(match_path, index=False, encoding="utf-8-sig")

    summary = {
        "input_rows": int(len(raw)),
        "cleaned_rows": int(len(cleaned)),
        "matched_image_dirs": int(matched["image_dir_exists"].sum()),
        "match_rate": float(matched["image_dir_exists"].mean()) if len(matched) else 0.0,
        "median_price_yuan_m2": float(matched["price_yuan_m2"].median()) if len(matched) else None,
        "outputs": {
            "clean": str(clean_path),
            "match": str(match_path),
        },
    }
    write_json(output_dir / "prepare_anjuke_summary.json", summary)
    return {"clean": clean_path, "match": match_path}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=None)
    parser.add_argument("--image-root", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--count-files", action="store_true", help="统计每个小区照片数量")
    parser.add_argument("--limit", type=int, default=None, help="仅用于冒烟测试")
    args = parser.parse_args()
    outputs = run_prepare(
        csv_path=args.csv,
        image_root=args.image_root,
        output_dir=args.output_dir,
        count_files=args.count_files,
        limit=args.limit,
    )
    print(outputs)


if __name__ == "__main__":
    main()
