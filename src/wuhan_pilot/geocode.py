"""地理编码：优先使用已有 2018 小区坐标按名称回填，其次调用高德/百度 API。"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable

import pandas as pd

from . import config
from .utils import ensure_dir, normalize_name, write_json


def load_historical_coordinates(xlsx_path: Path) -> pd.DataFrame:
    frame = pd.read_excel(xlsx_path)
    frame = frame.rename(
        columns={
            "小区名称": "community",
            "经度_百度坐标": "lng",
            "纬度_百度坐标": "lat",
        }
    )
    keep = ["community", "lng", "lat"]
    frame = frame[[col for col in keep if col in frame.columns]].copy()
    frame["name_key"] = frame["community"].map(normalize_name)
    frame["lng"] = pd.to_numeric(frame["lng"], errors="coerce")
    frame["lat"] = pd.to_numeric(frame["lat"], errors="coerce")
    frame = frame[(frame["lng"].notna()) & (frame["lat"].notna())].copy()
    frame = frame.drop_duplicates(subset=["name_key"]).set_index("name_key")
    return frame


def geocode_via_api(
    addresses: pd.Series,
    api_key: str | None,
    provider: str = "amap",
    timeout: float = 10.0,
    batch_size: int = 10,
) -> pd.DataFrame:
    """调用地图 API 地理编码；高德使用批量接口，百度逐条调用。"""
    try:
        import requests
    except ImportError as exc:
        raise RuntimeError("缺少 requests，请先安装：pip install requests") from exc

    if not api_key:
        raise RuntimeError("未提供 API key，无法调用地理编码服务")

    # 高德使用批量接口，每次最多 10 条地址，减少请求次数。
    rows = []
    session = requests.Session()
    addr_list = addresses.dropna().astype(str).tolist()

    if provider == "amap":
        url = "https://restapi.amap.com/v3/geocode/geo"
        for start in range(0, len(addr_list), batch_size):
            batch = addr_list[start:start + batch_size]
            # address 用竖线拼接，batch=true 表示批量查询。
            params = {"address": "|".join(batch), "key": api_key, "batch": "true", "city": "武汉"}
            data = session.get(url, params=params, timeout=timeout).json()
            geocodes = data.get("geocodes") or []
            for idx, address in enumerate(batch):
                lng = lat = None
                if idx < len(geocodes):
                    location = geocodes[idx].get("location", "")
                    if "," in location:
                        lng, lat = (float(v) for v in location.split(",")[:2])
                rows.append({"address": address, "lng": lng, "lat": lat})
        return pd.DataFrame(rows)

    for address in addr_list:
        if provider == "baidu":
            url = "https://api.map.baidu.com/geocoding/v3/"
            params = {"address": address, "ak": api_key, "output": "json", "city": "武汉市"}
        else:
            raise ValueError(f"不支持的 provider: {provider}")
        response = session.get(url, params=params, timeout=timeout)
        data = response.json()
        lng = lat = None
        result = data.get("result") or {}
        location = result.get("location") or {}
        lng = location.get("lng")
        lat = location.get("lat")
        rows.append({"address": address, "lng": lng, "lat": lat})
    return pd.DataFrame(rows)


def enrich_coordinates(
    communities: pd.DataFrame,
    historical: pd.DataFrame,
    api_callback: Callable[[pd.Series], pd.DataFrame] | None = None,
) -> pd.DataFrame:
    out = communities.copy()
    out["name_key"] = out["community"].map(normalize_name)
    out["lng_2018"] = out["name_key"].map(historical["lng"])
    out["lat_2018"] = out["name_key"].map(historical["lat"])
    out["lng"] = out["lng_2018"]
    out["lat"] = out["lat_2018"]
    out["coord_source"] = "2018_join"

    # 先用 2018 年坐标回填，剩余缺失再调 API。
    if api_callback is not None:
        missing_mask = out["lng"].isna()
        if missing_mask.any():
            api_result = api_callback(out.loc[missing_mask, "小区地址"].astype(str))
            keyed = api_result.drop_duplicates(subset=["address"]).set_index("address")
            for idx in out.index[missing_mask]:
                address = str(out.loc[idx, "小区地址"])
                if address in keyed.index and keyed.loc[address, "lng"] is not None:
                    out.loc[idx, "lng"] = keyed.loc[address, "lng"]
                    out.loc[idx, "lat"] = keyed.loc[address, "lat"]
                    out.loc[idx, "coord_source"] = "api"

    return out.drop(columns=["name_key"])


def run_geocode(
    community_csv: Path | None = None,
    historical_xlsx: Path | None = None,
    output_dir: Path | None = None,
    use_api: bool = False,
) -> dict[str, Path]:
    community_csv = Path(community_csv or (config.DATA_PROCESSED / config.OUTPUT_ANJUKE_CLEAN.name))
    historical_xlsx = Path(historical_xlsx or (config.HISTORICAL_CITY_PRICES / "武汉小区数据.xlsx"))
    output_dir = output_dir or config.DATA_PROCESSED
    ensure_dir(output_dir)

    communities = pd.read_csv(community_csv)
    historical = load_historical_coordinates(historical_xlsx)

    callback = None
    if use_api:
        import os
        # 密钥只从环境变量读取，不写进代码。
        api_key = os.getenv("AMAP_API_KEY") or os.getenv("BAIDU_API_KEY")
        provider = "amap" if os.getenv("AMAP_API_KEY") else "baidu"
        if not api_key:
            raise RuntimeError("未设置 AMAP_API_KEY 或 BAIDU_API_KEY 环境变量")
        callback = lambda series: geocode_via_api(series, api_key, provider=provider)

    result = enrich_coordinates(communities, historical, callback)
    out_path = output_dir / "communities_geocoded.csv"
    result.to_csv(out_path, index=False, encoding="utf-8-sig")

    summary = {
        "input_rows": int(len(communities)),
        "coordinate_matched": int(result["lng"].notna().sum()),
        "match_rate": float(result["lng"].notna().mean()) if len(result) else 0.0,
        "source_2018_join": int((result["coord_source"] == "2018_join").sum()),
        "source_api": int((result["coord_source"] == "api").sum()),
        "output": str(out_path),
    }
    write_json(output_dir / "geocode_summary.json", summary)
    return {"output": out_path}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--community-csv", type=Path, default=None)
    parser.add_argument("--historical-xlsx", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--use-api", action="store_true")
    args = parser.parse_args()
    run_geocode(
        community_csv=args.community_csv,
        historical_xlsx=args.historical_xlsx,
        output_dir=args.output_dir,
        use_api=args.use_api,
    )


if __name__ == "__main__":
    main()




