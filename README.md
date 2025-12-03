# STEM + Atomap GUI (v0.1.0)

基于 Atomap 的 STEM 原子定位与位移计算骨架，带 PySide6 前端。核心算法封装在 `core/`，前端在 `ui_qt/`，命令行测试在 `tests/`。输入数据默认放在 `./data`。

This is an Atomap-based STEM atomic position and displacement analysis scaffold with a PySide6 GUI. Core logic lives in `core/`, GUI in `ui_qt/`, CLI tests in `tests/`. Default input data directory: `./data`.

## 功能概览 / Features
- 读取 STEM/HAADF 2D 图像（dm3/dm4/tif/jpg），可选比例尺（nm/px）。  
  Load STEM/HAADF 2D images (dm3/dm4/tif/jpg) with optional scale (nm/px).
- 预处理：高斯平滑（可调）、归一化。  
  Preprocess with Gaussian smoothing (tunable) and normalization.
- 晶格估计：FFT 估分离度，构建 A 子晶格，四邻中心生成理想 B 位。  
  Lattice estimation via FFT, build A sublattice, ideal B from neighboring centers.
- 位置精炼：A/B 子晶格精炼，得到实际 B 位坐标。  
  Refine A/B sublattices to get actual B coordinates.
- 位移计算：B 相对理想中心的偏移向量（dx, dy），可换算 nm；箭头图、插值热图。  
  Displacement vectors of B vs ideal centers (dx, dy), optional nm conversion; arrows and interpolated heatmap.
- 输出：按输入图像名生成 `outputs/<图像名>/`，保存预处理图、A/B 坐标、叠加、位移 CSV/箭头/热图；日志 `log/app.log`。  
  Outputs to `outputs/<image-name>/`: preprocessed image, A/B coords, overlays, displacement CSV/arrows/heatmap; logs in `log/app.log`.
- GUI：预览、参数与比例尺输入、状态栏、A/B 叠加、位移箭头、热图。  
  GUI with preview, parameter & scale inputs, status bar, A/B overlay, displacement arrows, heatmap.

## 目录结构 / Structure
- `main.py`：Qt 前端入口 / Qt app entry.
- `config.py`：默认参数 / default params.
- `core/`：预处理、A/B 子晶格、位移、可视化 / preprocessing, sublattices, displacement, viz.
- `ui_qt/`：PySide6 界面 / GUI.
- `tests/`：命令行测试 / CLI tests.
- `log/`：运行日志 / logs.
- `outputs/`：输出目录（按输入文件名分文件夹）/ outputs by image name.
- `VERSION`：当前版本号（0.1.0）。

## 安装 / Install
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## GUI 运行 / Run GUI
```bash
python main.py
```
步骤：选择图像 → 设置参数/比例尺 → 运行；界面显示 A/B 叠加、位移箭头、热图，状态栏显示输出目录；日志在 `log/app.log`。  
Steps: choose image → set params/scale → run; GUI shows overlays/arrows/heatmap, status bar shows output dir; logs in `log/app.log`.

## 命令行测试 / CLI Test
```bash
python tests/test_pipeline.py
# 可选参数 / optional:
# --image data/xxx.dm3 --output tests/output --nm-per-pixel 0.02 --arrow-scale 50
```
输出包括 / Outputs: `preprocessed.png`, `peaks_a/b.csv`, `peaks_overlay.png`, `displacement.csv` (px, optional nm), `displacement_arrows.png`, `displacement_heatmap.png`。

## 算法流程 / Algorithm
1) 预处理：高斯平滑 + 归一化。  
2) FFT 估分离度（可手动指定）。  
3) A 子晶格：峰检测 + zone axes。  
4) 理想 B 位：四邻中心；构建 B 子晶格并精炼。  
5) 位移：`dx, dy = peaks_b - ideal_b`，模长 `|d|`，可换算 nm。  
6) 可视化：A/B 叠加、位移箭头（可放大）、位移模长插值热图；输出写入 `outputs/<图像名>/`。  

1) Preprocess (Gaussian + normalize).  
2) FFT estimate separation (or manual).  
3) A sublattice via peak detection + zone axes.  
4) Ideal B from neighbor centers; build/refine B sublattice.  
5) Displacement `dx, dy = peaks_b - ideal_b`, magnitude `|d|`, optional nm.  
6) Viz: A/B overlay, arrows (scalable), interpolated heatmap; saved to `outputs/<image-name>/`.
