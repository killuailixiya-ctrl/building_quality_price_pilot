"""在 ArcGIS Pro 环境中从 OSM 路网生成道路街区。"""

from __future__ import annotations

import argparse
from pathlib import Path


def build_blocks(road_network: str, research_area: str, output_gdb: str) -> None:
    try:
        import arcpy
    except ImportError as exc:
        raise RuntimeError(
            "本脚本需要在 ArcGIS Pro 的 Python 环境中运行。请使用 arcpy 环境执行。"
        ) from exc

    arcpy.env.overwriteOutput = True
    arcpy.env.workspace = output_gdb

    if not arcpy.Exists(output_gdb):
        arcpy.management.CreateFileGDB(str(Path(output_gdb).parent), Path(output_gdb).name)

    roads_clip = str(Path(output_gdb) / "roads_clip")
    arcpy.analysis.Clip(road_network, research_area, roads_clip)

    roads_clean = str(Path(output_gdb) / "roads_clean")
    arcpy.management.RepairGeometry(roads_clip)
    arcpy.management.Dissolve(roads_clip, roads_clean)

    blocks_raw = str(Path(output_gdb) / "blocks_raw")
    arcpy.management.FeatureToPolygon(roads_clean, blocks_raw, attributes="NO_ATTRIBUTES")

    blocks = str(Path(output_gdb) / "blocks")
    arcpy.management.MultipartToSinglepart(blocks_raw, blocks)
    arcpy.management.AddField(blocks, "block_id", "TEXT", field_length=32)
    arcpy.management.CalculateField(
        blocks,
        "block_id",
        expression="'B' + str(!OBJECTID!)",
        expression_type="PYTHON3",
    )

    centroids = str(Path(output_gdb) / "block_centroids")
    arcpy.management.FeatureToPoint(blocks, centroids, "INSIDE")
    print(f"blocks: {blocks}")
    print(f"centroids: {centroids}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--road-network", required=True)
    parser.add_argument("--research-area", required=True)
    parser.add_argument("--output-gdb", required=True)
    args = parser.parse_args()
    build_blocks(args.road_network, args.research_area, args.output_gdb)


if __name__ == "__main__":
    main()

