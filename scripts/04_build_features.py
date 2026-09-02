"""在 ArcGIS Pro 环境中构建街区级客观变量和特征矩阵。"""

from __future__ import annotations

import argparse
from pathlib import Path


def build_features(
    geocoded_csv: str,
    blocks: str,
    poi_csv: str,
    metro_dir: str,
    ndvi_dir: str,
    landcover_dir: str,
    output_gdb: str,
    output_csv: str,
) -> None:
    try:
        import arcpy
        from arcpy.sa import Idw, ZonalStatisticsAsTable
    except ImportError as exc:
        raise RuntimeError(
            "本脚本需要在 ArcGIS Pro 的 Python 环境中运行，并启用 Spatial Analyst 扩展。"
        ) from exc

    arcpy.env.overwriteOutput = True
    arcpy.env.workspace = output_gdb
    arcpy.CheckOutExtension("Spatial")

    communities_points = str(Path(output_gdb) / "communities_points")
    arcpy.management.XYTableToPoint(
        geocoded_csv,
        communities_points,
        x_field="lng",
        y_field="lat",
        coordinate_system=arcpy.SpatialReference(4326),
    )

    communities_projected = str(Path(output_gdb) / "communities_projected")
    arcpy.management.Project(communities_points, communities_projected, arcpy.SpatialReference(4547))

    joined = str(Path(output_gdb) / "communities_block_join")
    arcpy.analysis.SpatialJoin(
        communities_projected,
        blocks,
        joined,
        join_operation="JOIN_ONE_TO_ONE",
        join_type="KEEP_ALL",
        match_option="INTERSECT",
    )

    idw_price = Idw(communities_projected, "price_yuan_m2", cell_size=500, power=2)
    idw_age = Idw(communities_projected, "age_years", cell_size=500, power=2)
    idw_far = Idw(communities_projected, "floor_area_ratio", cell_size=500, power=2)

    for raster, field, name in [
        (idw_price, "price_yuan_m2", "block_price"),
        (idw_age, "age_years", "block_age"),
        (idw_far, "floor_area_ratio", "block_far"),
    ]:
        zonal_table = str(Path(output_gdb) / f"zonal_{name}")
        ZonalStatisticsAsTable(blocks, "block_id", raster, zonal_table, "DATA", "MEAN")

    print("IDW/zonal outputs written to", output_gdb)
    print("下一步：合并 zonal 表、POI 密度、地铁距离和 NDVI/土地覆盖指标，生成", output_csv)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--geocoded-csv", required=True)
    parser.add_argument("--blocks", required=True)
    parser.add_argument("--poi-csv", required=True)
    parser.add_argument("--metro-dir", required=True)
    parser.add_argument("--ndvi-dir", required=True)
    parser.add_argument("--landcover-dir", required=True)
    parser.add_argument("--output-gdb", required=True)
    parser.add_argument("--output-csv", required=True)
    args = parser.parse_args()
    build_features(
        args.geocoded_csv,
        args.blocks,
        args.poi_csv,
        args.metro_dir,
        args.ndvi_dir,
        args.landcover_dir,
        args.output_gdb,
        args.output_csv,
    )


if __name__ == "__main__":
    main()

