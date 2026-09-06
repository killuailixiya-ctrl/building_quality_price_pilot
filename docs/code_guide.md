# 代码与参数说明

本文件帮助你理解每个脚本在做什么、哪些参数可以调整、哪些地方容易出错。

## 运行环境

- Python：`E:\02_install_Professional_Software\ArcgisPro\bin\Python\envs\arcgispro-py3\python.exe`
- 当前预实验：武汉 2022，因变量只有房价。
- 主要空间单元：OSM 道路围合街区。

## 核心脚本顺序

| 脚本 | 作用 | 关键参数 |
|---|---|---|
| `00_data_inventory.py` | 检查原始数据是否存在 | 无 |
| `01_prepare_anjuke.py` | 清洗安居客数据，匹配照片 | `--count-files` 是否统计照片数 |
| `02_geocode.py` | 补全小区坐标 | `--use-api` 是否使用高德/百度 API |
| `03_build_blocks.py` | 用路网生成街区 | `--road-network`、`--research-area`、`--output-gdb` |
| `04_build_features.py` | 用 ArcGIS 做 IDW/分区统计 | 路径参数 |
| `05_image_quality.py` | 早期 PIL 图像启发式品质分 | `--max-communities`、`--max-per-community` |
| `06_modeling.py` | 简单房价模型 | `--feature-csv`、`--target` |
| `07_build_feature_matrix_geopandas.py` | 早期最小特征矩阵 | 无 |
| `08_build_full_features.py` | 生成完整街区特征矩阵 | 无 |
| `09_clip_building_score.py` | CLIP 尝试，未使用 | 无 |
| `10_local_efficientnet_score.py` | 本地 EfficientNet 建筑品质分 | `--max-communities`、`--max-per-community` |
| `11_add_raster_features.py` | 加 NDVI、绿地、水域 | 无 |
| `12_full_models.py` | 早期多模型 | 无 |
| `13_vif_selection.py` | VIF 筛选 | `--input`、`--output-csv`、`--output-json` |
| `14_final_models.py` | OLS/RF/GWRF/GWR 最终模型 | `--input`、`--output-json` |
| `15_building_segmentation.py` | 单张建筑语义分割 | `--max-communities`、`--max-per-community` |
| `16_batch_segmentation.py` | 批量建筑语义分割 | `--batch-size` |
| `17_use_idw_features.py` | 用 IDW 分区统计替换简单均值 | 无 |
| `18_shap_pdp.py` | 输出 SHAP/PDP | 无 |
| `19_idw_pipeline.py` | 保存 IDW 栅格 | 无 |
| `20_idw_v3.py` | 更大搜索半径的 IDW | 无 |
| `21_add_ring_scope.py` | 加三环线范围/距离 | 无 |

## 关键参数说明

### 建筑品质分参数

- `image_efficientnet_scores.csv` 中每一行是一张图片的分数。
- `building_score_mean` 是按 `community_id` 聚合后的平均品质分，再聚合到 `block_id`。
- `building_image_count` 是参与聚合的图片数量。
- 如果未来改成人工 TrueSkill 建筑质量分，只需要替换输入分数表和聚合字段。

### 模型参数

- `14_final_models.py` 中：
  - OLS：`sm.OLS`
  - RF：`RandomForestRegressor(n_estimators=300)`
  - GWRF：`PyGRFBuilder(band_width=100, n_estimators=50)`
  - GWR：`number_of_neighbors=100`
- 随机种子固定为 `42`，方便复现。

## 容易出错的地方

1. `14_final_models.py` 的 GWR 输出字段是 `PREDICTED`，不是 `Predicted`。
2. `feature_matrix.csv` 会被多个脚本覆盖，顺序必须是：
   - `08_build_full_features.py`
   - `11_add_raster_features.py`
   - `17_use_idw_features.py`
   - `21_add_ring_scope.py`
   - `13_vif_selection.py`
   - `14_final_models.py`
3. 如果使用高德 Key，请用环境变量 `AMAP_API_KEY`，不要把 Key 写进代码。
4. 三环线面数据使用 `Id=3`，如果换城市或换年份需要确认对应环线。

