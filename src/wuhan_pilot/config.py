"""集中管理路径和参数。

实现阶段先以本文件为主，`params.yaml` 供人类阅读和跨语言使用。
"""

from __future__ import annotations

from pathlib import Path


# 原始数据根目录，所有外部数据都在这里。
RAW_ROOT = Path("E:/刘天辰")
# 项目根目录：D:/Codex/building_01
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# 项目内部目录
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
IMAGES_DIR = PROJECT_ROOT / "images"
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"

ANJUKE_CSV = RAW_ROOT / "POI以及房价时序数据/安居客房价202209/data202209.csv"
COMMUNITY_IMAGES_ROOT = RAW_ROOT / "社区照片/img"
ROAD_NETWORK = RAW_ROOT / "2022OSM路网数据/roadnetOSM2022.shp"
RESEARCH_AREA = RAW_ROOT / "2022OSM路网数据/research_area.shp"
POI_2021_CSV = RAW_ROOT / "POI以及房价时序数据/POI武汉10-20/2021-湖北省-武汉市.csv"
POI_2023_DIR = RAW_ROOT / "武汉POI/2023"
METRO_DIR = RAW_ROOT / "武汉地铁数据"
NDVI_DIR = RAW_ROOT / "武汉NDVI"
LANDCOVER_DIR = RAW_ROOT / "土地覆盖类型"
ADMIN_DIR = RAW_ROOT / "行政区划"
GIS_BASE_DIR = RAW_ROOT / "GIS基底数据"
HISTORICAL_CITY_PRICES = RAW_ROOT / "01熊秀海/03-房价数据/小区房价数据"

# 当前预实验城市和年份。
CITY = "武汉"
YEAR = 2022
TARGET_BLOCKS = 500
MIN_BLOCKS = 300
RANDOM_SEED = 42

# 中间结果输出文件。
OUTPUT_ANJUKE_CLEAN = DATA_PROCESSED / "anjuke_2022_clean.csv"
OUTPUT_COMMUNITY_MATCH = DATA_PROCESSED / "community_image_match.csv"
OUTPUT_FEATURE_MATRIX = DATA_PROCESSED / "feature_matrix.csv"
OUTPUT_MODEL_METRICS = REPORTS_DIR / "model_metrics.csv"
OUTPUT_RUN_DIR = REPORTS_DIR / "runs"

ARCGIS_PYTHON = Path("E:/02_install_Professional_Software/ArcgisPro/bin/Python/envs/arcgispro-py3/python.exe")
STREETVIEW_IMAGE_ROOTS = {2014: Path("E:/刘天辰/裁剪/2014"), 2015: Path("E:/刘天辰/裁剪/2015"), 2016: Path("E:/刘天辰/裁剪/2016"), 2017: Path("E:/刘天辰/裁剪/2017"), 2019: Path("F:/2019"), 2020: Path("F:/2020"), 2021: Path("F:/2021"), 2022: Path("F:/2022")}
ARCGIS_PROJECT_GDB = DATA_PROCESSED / "wuhan_blocks.gdb"
