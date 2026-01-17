# STEM Atomap GUI User Manual

This manual provides a detailed guide on using the STEM Atomap GUI software for analyzing atomic-resolution STEM images. The software utilizes the open-source `atomap` library to quantify atomic positions, displacements, and strain fields.

[TOC]

## 1. Introduction

**STEM Atomap GUI** is a desktop application designed for material scientists to analyze Scanning Transmission Electron Microscopy (STEM) images. It automates the process of:

- Detecting atomic column positions (sublattices).
- Measuring deviations from ideal lattice positions (polarization/displacement).
- Mapping strain fields (εxx, εyy, εxy, rotation).
- Generating publication-quality visualizations with statistical analysis.

## 2. Interface Overview

The main window consists of two areas:

1. **Left Sidebar (Controls)**: File selection, parameter settings, and execution controls.
2. **Right Panel (Results)**: Tabbed interface displaying analysis results.

### Result Tabs

- **Overview**: Basic quality checks (Raw image, Atom detection overlay, Displacement vector map, Magnitude heatmap).
- **Color Vectors**: Advanced vector maps colored by angle (HSV wheel) or magnitude.
- **Statistics**: Displacement magnitude histograms (with Gaussian fit) and polar plots of displacement directions.
- **Strain Analysis**: Maps of strain tensor components (εxx, εyy, εxy) and lattice rotation.

## 3. Workflow & Parameters

### Step 1: Load Image

Click **"Select Image"** to load a `.dm3`, `.dm4`, `.tif`, or `.png` file.
> **Note**: For `.dm3`/`.dm4` files, the software automatically reads pixel size (scale) metadata.

### Step 2: Set Parameters

Configure the analysis parameters in the sidebar. Hover over any input field for a tooltip explanation.

| Parameter | Unit | Default | Description |
| :--- | :--- | :--- | :--- |
| **Gaussian σ** | px | 1.0 | Standard deviation for Gaussian smoothing during preprocessing. Increase for noisy images. |
| **Refine σ** | px | 1.0 | Sigma used for 2D Gaussian peak fitting during atomic position refinement. |
| **Separation** | px | Auto | **Crucial**. Estimated minimum distance between atoms. <br>• **Empty**: Auto-calculated using FFT (Recommended for standard lattices).<br>• **Manual**: Set a value (e.g., 15) if auto-detection fails or for complex structures. |
| **Threshold** | 0-1 | Auto | Relative threshold for peak detection. Lower values detect weaker peaks; higher values reduce false positives. |
| **Scale** | nm/px | Auto | Physical pixel size. Auto-read from metadata. <br>• Enter manually to override (e.g., `0.02`). Required for scale bars and correct strain units. |

### Step 3: Run Analysis

Click **"Run"**. The status bar will show "Running...", and results will appear in the tabs upon completion.
> **Status**: The status bar also displays the estimated resolution/separation after a successful run.

### Step 4: Export

Click **"Export Results"** to save all generated plots and CSV data to the output directory.
Default location: `outputs/<image_filename>/`

## 4. Algorithm & Calculations

### 4.1. Atom Detection

1. **Preprocessing**: Background subtraction and Gaussian smoothing.
2. **Lattice Estimation**: Unless manually specified, FFT (Fast Fourier Transform) estimates the primary lattice periodicity (`Separation`).
3. **Sublattice Identification**:
    - **Sublattice A**: Detected using local maxima search.
    - **Sublattice B**: Defined as the center points of Sublattice A's neighbors (detecting the interstitial or secondary atoms).
4. **Refinement**: Positions are refined to sub-pixel accuracy using Center of Mass (CoM) or 2D Gaussian fitting.

### 4.2. Displacement Calculation

Calculates the vector $\mathbf{u} = \mathbf{r}_B - \mathbf{r}_{ideal$, where $\mathbf{r}_B$ is the detected position of atom B, and $\mathbf{r}_{ideal}$ is the geometric center of its surrounding A neighbors.

- **Magnitude**: $|\mathbf{u}| = \sqrt{dx^2 + dy^2}$
- **Angle**: $\theta = \arctan2(dy, dx)$

### 4.3. Strain Mapping

Strain is derived from the gradients of the displacement field $\mathbf{u}(x,y) = (u,v)$.

- $\varepsilon_{xx} = \frac{\partial u}{\partial x}$
- $\varepsilon_{yy} = \frac{\partial v}{\partial y}$
- $\varepsilon_{xy} = \frac{1}{2}(\frac{\partial u}{\partial y} + \frac{\partial v}{\partial x})$ (Shear strain)
- $\omega = \frac{1}{2}(\frac{\partial v}{\partial x} - \frac{\partial u}{\partial y})$ (Rotation, radians)

> **Edge Handling**: To avoid artifacts, the software uses **Convex Hull Masking**. Areas outside the valid atom region (shrunk by 10%) are masked out (white/transparent).

## 5. Output Files

Each run generates the following in the output folder:

| File | Description |
| :--- | :--- |
| `preprocessed.png` | Image used for detection. |
| `peaks_overlay.png` | Original image with A (red) and B (blue) atomic positions. |
| `displacement_arrows_angle.png` | Vectors colored by direction (HSV). |
| `displacement_heatmap.png` | Interpolated map of displacement magnitude. |
| `displacement_histogram.png` | Statistical distribution of magnitudes. |
| `strain_combined.png` | 2x2 panel of all strain components. |
| `peaks_a.csv`, `peaks_b.csv` | Raw atomic coordinates (x, y). |
| `displacement.csv` | Calculated displacements for each B atom. |
| `statistics.txt` | Summary statistics (mean, std dev). |

## 6. Troubleshooting

- **"Not enough zone axes detected"**: The algorithm couldn't find the lattice symmetry.
  - *Fix*: Ensure `Separation` is correct (try manual input). Check if the image contrast is inverted (atoms should be bright).
- **Messy/Wrong Arrows**:
  - *Fix*: Check `peaks_overlay.png`. If atoms are missed, lower `Threshold`. If noise is picked up, increase `Threshold` or `Gaussian σ`.
- **Wrong Scale**:
  - *Fix*: Manually enter the correct `nm/px` value from microscope software.

## 7. Dependencies

- Python 3.9+
- `atomap`, `hyperspy`, `numpy`, `scipy`, `matplotlib`, `pyside6`
