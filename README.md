# 武汉 2022 住区建筑品质—房价预实验

本仓库用于验证“建筑图像 → 建筑品质代理分 → 道路街区聚合 → 房价建模”的技术路线。预实验以武汉 2022 年横断面为对象，暂不做租金；正式研究再扩展到北京、上海、广州、武汉 2024 年四城比较。

## 目录

- `data/raw`：原始数据登记，不直接提交大文件。
- `data/processed`：清洗、匹配、聚合后的中间结果。
- `images`：建筑图像清单、分类结果和品质评分表。
- `src/wuhan_pilot`：可复用的 Python 包。
- `scripts`：按阶段执行入口。
- `docs`：研究协议、数据字典、决策日志、模型卡。
- `reports`：预实验报告和图表。

## 快速开始

1. 在 ArcGIS Pro 的 Python 环境或满足 `environment.yml` 的环境中安装依赖。
2. 确认 `G:\huanghaojun_buliding` 数据可读，并检查 `src/wuhan_pilot/config.py` 中的路径。
3. 运行：

```powershell
python scripts/00_data_inventory.py
python scripts/01_prepare_anjuke.py
```

完整流程见 `docs/research_protocol.md`。

