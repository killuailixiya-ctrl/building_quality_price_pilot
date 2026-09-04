# 未来建筑品质评分模型训练方案

## 来源

- `E:\刘天辰\PlacePulseDataset.py`
- `E:\刘天辰\质量训练_划分.py`

## 作用

用建筑图像的 TrueSkill 主观评分训练 ShuffleNetV2 回归模型，并生成建筑品质分。

## 何时启用

当以下内容准备好后启用：

1. 建筑图像目录。
2. 建筑图像的成对比较结果，并转为 `final_ratings.csv`。
3. 该 CSV 至少包含：
   - `pic_id`
   - `trueskill.score`

## 接入时需要修改

- `img_dir`：改为建筑图像目录。
- `trueskill_score_csv_path`：改为建筑图 `final_ratings.csv`。
- 输出目录：改为 `D:\Codex\building_01\models`。
- 安装 `albumentations`。

## 需要用户后续提供

- 建筑图片的人工成对比较结果，或对应的 TrueSkill 分数表。
