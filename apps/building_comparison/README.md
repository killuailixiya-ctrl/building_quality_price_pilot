# 建筑图片两两对比平台

用于对建筑图片做主观偏好成对比较，结果用 TrueSkill 转化为连续评分。

## 本地运行

```powershell
cd D:\Codex\building_01\apps\building_comparison
& "E:\02_install_Professional_Software\ArcgisPro\bin\Python\envs\arcgispro-py3\python.exe" -m streamlit run app.py
```

## 对比数量

当前准备了 200 张建筑图片。

- 完全遍历：C(200, 2) = 19,900 次。
- 论文也使用了 19900 次对比。
- 如果人手不足，也可以设置目标为每张图片比较 20-36 次。

## 结果

对比结果保存在 `comparison_results.csv`。
