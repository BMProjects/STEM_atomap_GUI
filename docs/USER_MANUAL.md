# STEM Atomap GUI User Manual / 用户手册

**Bilingual User Manual for STEM Atomap GUI**
**STEM Atomap GUI 双语用户手册**

This manual provides a detailed guide on using the software for analyzing atomic-resolution STEM images.
本手册详细介绍了如何使用该软件分析原子分辨率 STEM 图像。

[TOC]

## 1. Introduction / 简介

**STEM Atomap GUI** is a desktop application designed for material scientists to analyze Scanning Transmission Electron Microscopy (STEM) images.
**STEM Atomap GUI** 是一款专为材料科学家设计的桌面应用程序，用于分析扫描透射电子显微镜 (STEM) 图像。

It automates / 它可以自动化以下过程:

- Detecting atomic column positions (sublattices). / 检测原子列位置（子晶格）。
- Measuring deviations from ideal lattice positions (displacement). / 测量偏离理想晶格位置的偏差（位移）。
- Mapping strain fields (εxx, εyy, εxy, rotation). / 绘制应变场（εxx, εyy, εxy, 旋转）。
- Generating visualizations and statistics. / 生成可视化图表和统计数据。

## 2. Interface Overview / 界面概览

The main window consists of two areas:
主窗口包含两个区域：

1. **Left Sidebar (Controls)**: File selection, parameter settings, and execution controls.
    **左侧边栏（控制面板）**：文件选择、参数设置和执行控制。
2. **Right Panel (Results)**: Tabbed interface displaying analysis results.
    **右侧面板（结果展示）**：分页显示的分析结果。

### Result Tabs / 结果标签页

- **Overview (概览)**: Basic quality checks (Raw image, Overlays, Heatmap). / 基础检查（原图、叠加图、热图）。
- **Colored Vectors (彩色矢量图)**: Advanced vectors colored by angle/magnitude. / 按角度或模长着色的矢量图。
- **Statistics (统计分布)**: Histograms and polar plots. / 直方图和极图。
- **Strain Analysis (应变分析)**: Maps of strain tensor components. / 应变张量分量图。

## 3. Workflow & Parameters / 工作流程与参数

### Step 1: Load Image / 加载图像

Click **"Select Image"** to load a `.dm3`, `.dm4`, `.tif`, or `.png` file.
点击 **"Select Image"** 加载图像文件。

### Step 2: Set Parameters / 设置参数

| Parameter (参数) | Unit | Default | Description (说明) |
| :--- | :--- | :--- | :--- |
| **Gaussian σ** | px | 1.0 | Smoothing sigma. Increase for noisy images. <br> 平滑参数，噪点多时调大。 |
| **Refine σ** | px | 1.0 | Sigma for peak refinement fitting. <br> 峰值精修拟合的 Sigma。 |
| **Separation** | px | Auto | **Crucial**. Estimated atomic distance. Empty=Auto (FFT). <br> **关键参数**。估计的原子间距。留空则自动计算。 |
| **Threshold** | 0-1 | Auto | Peak detection threshold. <br> 峰值检测阈值。 |
| **Scale** | nm/px | Auto | Physical pixel size. Auto-read from metadata. <br> 物理像素尺寸。通常自动读取。 |

### Step 3: Run Analysis / 运行分析

Click **"Run"**. Status bar shows "Running...".
点击 **"Run"**。状态栏显示 "Running..."。

### Step 4: Export / 导出

Click **"Export Results"** to save to `outputs/`.
点击 **"Export Results"** 保存结果到 `outputs/` 目录。

## 4. Algorithm / 算法原理

### 4.1. Atom Detection / 原子检测

1. **Preprocessing**: Background subtraction & Gaussian smoothing. (预处理：去背景与平滑)
2. **Lattice Estimation**: FFT estimates periodicity (`Separation`). (FFT 估算周期)
3. **Sublattice B**: Defined as centers of A's neighbors. (B 子晶格定义为 A 的邻域中心)

### 4.2. Displacement / 位移计算

Vector $\mathbf{u} = \mathbf{r}_B - \mathbf{r}_{ideal}$.
向量 $\mathbf{u}$ 为 B 原子实际位置减去理想位置。

### 4.3. Strain Mapping / 应变映射

Derived from displacement gradients.
基于位移梯度计算。

> **Edge Handling**: **Convex Hull Masking** is used to hide artifacts at edges.
> **边缘处理**：使用**凸包遮罩**隐藏边缘伪影。

## 5. Output Files / 输出文件

| File | Description |
| :--- | :--- |
| `preprocessed.png` | Preprocessed image / 预处理图像 |
| `peaks_overlay.png` | A(red)/B(blue) peaks overlay / 原子位置叠加图 |
| `displacement_heatmap.png` | Magnitude heatmap / 位移热图 |
| `strain_combined.png` | Strain tensor panel / 应变张量面板 |
| `displacement.csv` | Raw displacement data / 位移数据 CSV |

## 6. Troubleshooting / 故障排除

- **"Not enough zone axes..."**:
  - Try manual `Separation`. / 尝试手动输入 Separation。
- **Messy Arrows**:
  - Adjust `Threshold` or `Gaussian σ`. / 调整阈值或平滑参数。
- **Wrong Units**:
  - Manually enter `Scale`. / 手动输入 Scale。
