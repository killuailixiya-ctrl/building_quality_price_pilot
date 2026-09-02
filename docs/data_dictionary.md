# 数据字典

## 原始数据

| 名称 | 路径 | 年份/版本 | 关键字段 |
|---|---|---|---|
| 安居客武汉小区数据 | `data202209.csv` | 2022-09 | `community_id`, `community`, `area`, `price`, `容积率`, `物业费`, `竣工时间`, `小区地址` |
| 小区建筑照片 | `社区照片/img/<community_id>/` | 未知 | 图片文件名 `<community_id>_<seq>.jpg` |
| 2022 OSM 路网 | `roadnetOSM2022.shp` | 2022 | 道路几何、道路等级 |
| 武汉 POI | `2021-湖北省-武汉市.csv` | 2021 | `名称`, `类型1`, `类型2`, `百度X`, `百度Y` |
| 武汉 POI 分类 | `武汉POI/2023/*.shp` | 2023 | 分类图层 |
| 地铁 | `武汉地铁数据/运行线路` | 历年 | 线路、站点 |
| NDVI | `武汉NDVI/*.tif` | 2023 | 栅格 NDVI |
| 土地覆盖 | `土地覆盖类型/*.tif` | 2000/2010/2020 | 栅格类别 |

## 派生字段

| 字段 | 类型 | 单位 | 说明 |
|---|---|---|---|
| `community_id` | int | - | 安居客小区编号，与照片目录一致 |
| `price_yuan_m2` | float | 元/㎡ | 清理后的挂牌均价 |
| `age_years` | float | 年 | 由竣工时间计算 |
| `property_score` | float | 1-5 | 物业费映射，或原始物业费标准化 |
| `building_score` | float | 标准化分 | 建筑品质代理分 |
| `block_id` | string | - | 道路街区编号 |
| `block_price` | float | 元/㎡ | IDW 聚合后的街区房价 |

字段清洗规则和缺失处理写入 `docs/decision_log.md`。
