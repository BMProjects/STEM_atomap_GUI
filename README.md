# STEM + Atomap GUI (v0.1.0)

基于 Atomap 的 STEM 原子定位与位移计算骨架，带 PySide6 前端。核心算法封装在 `core/`，前端在 `ui_qt/`，命令行测试在 `tests/`。

## 功能概览
- 读取 STEM/HAADF 2D 图像（dm3/dm4/tif/jpg），支持可选比例尺（nm/px）。
- 预处理：高斯平滑（可调）、归一化。
- 晶格估计：FFT 估算晶格分离度；构建 A 子晶格；以四邻居几何中心生成理想 B 位。
- 位置精炼：A/B 子晶格精炼，得到实际 B 位坐标。
- 位移计算：计算 B 相对理想中心的偏移向量（dx, dy），可选换算 nm；输出箭头图和插值位移热图。
- 输出：自动按输入图像名生成 `outputs/<图像名>/`，保存预处理图、A/B 坐标、叠加图、位移 CSV/箭头/热图；日志写入 `log/app.log`。
- GUI：图像预览、参数输入、比例尺输入、状态栏提示、A/B 叠加、位移箭头、位移热图展示。

## 目录结构
- `main.py`：Qt 前端入口。
- `config.py`：默认参数。
- `core/`：算法与可视化工具（预处理、A/B 子晶格、位移/热图/箭头输出）。
- `ui_qt/`：PySide6 界面。
- `tests/`：命令行测试脚本与默认输出目录。
- `log/`：运行日志。
- `outputs/`：默认输出目录（按输入文件名分文件夹）。
- `VERSION`：当前版本号（0.1.0）。

## 安装
```bash
python -m venv .venv
source .venv/bin/activate  # Windows 用 .venv\Scripts\activate
pip install -r requirements.txt
```

## GUI 运行
```bash
python main.py
```
步骤：选择图像 → 设置参数/比例尺 → 运行。完成后界面显示 A/B 叠加、位移箭头、位移热图，状态栏显示输出目录，日志在 `log/app.log`。

## 命令行测试
使用示例图跑全流程并输出到 `tests/output`：
```bash
python tests/test_pipeline.py
# 可选参数：
# --image data/xxx.dm3 --output tests/output --nm-per-pixel 0.02 --arrow-scale 50
```
输出包括：`preprocessed.png`、`peaks_a/b.csv`、`peaks_overlay.png`、`displacement.csv`（px，可选 nm）、`displacement_arrows.png`、`displacement_heatmap.png`。

## 算法流程（核心）
1) 读取图像并预处理（高斯平滑+归一化）。
2) FFT 估计晶格分离度（可手动指定）。
3) A 子晶格：峰检测 → 构建 zone axes。
4) B 理想位：四邻居中心点生成；构建 B 子晶格并精炼。
5) 位移：`dx, dy = peaks_b - ideal_b`，模长 `|d|`；可选 nm 换算。
6) 可视化：A/B 叠加、位移箭头（可放大）、位移模长插值热图；标准输出写入 `outputs/<图像名>/`。

## 流程概览
1) 读入 STEM/HAADF 图像（支持 dm3/tif/jpg）。  
2) 预处理：平场/背景去除、滤波、可选 ROI。  
3) FFT/自相关估计格矢初值。  
4) Atomap 峰检测与 `Atom_Lattice` 构建，亚像素精炼。  
5) 生成参考晶格，输出位移场/应变图与质量指标。  
6) 前端展示和导出 CSV/PNG。
