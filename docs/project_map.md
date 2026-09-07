# 项目文件地图

## 流程总览

```mermaid
flowchart TD
  A[原始数据 G 盘] --> B[01 数据清洗与照片匹配]
  B --> C[02 地理编码]
  B --> D[03 道路街区]
  D --> E[04/08 街区特征]
  C --> E
  E --> F[建筑图像品质分]
  F --> G[语义分割过滤]
  G --> E
  E --> H[NDVI/绿地/水域]
  E --> I[IDW 与三环线]
  I --> J[VIF 筛选]
  J --> K[OLS/GWR/RF/GWRF]
  K --> L[SHAP/PDP 图]
```

## 文件分组

| 前缀/目录 | 作用 |
|---|---|
| `scripts/00-02` | 数据准备：盘点、清洗、地理编码 |
| `scripts/03-04` | ArcGIS 街区、IDW、分区统计 |
| `scripts/05-10` | 图像品质分 |
| `scripts/11-21` | 栅格、环线、特征、VIF、模型 |
| `scripts/22-39` | 图表、多年份、动态 POI、三镇模型、GWR/GWRF |
| `src/wuhan_pilot` | 核心函数 |
| `data/raw` | 原始数据登记 |
| `data/processed` | 中间和最终特征表 |
| `images` | 图像评分和分割结果 |
| `reports` | 指标和图 |
| `docs` | 研究协议、数据字典、决策日志、文件地图 |
