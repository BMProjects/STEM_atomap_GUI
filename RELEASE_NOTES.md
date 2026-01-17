# Release Notes - v0.2.0

## 🌟 Highlights

This release introduces significant enhancements to visualization and usability, transforming the tool from a basic script into a comprehensive analysis suite for STEM atomic imagery.

- **Advanced Strain Mapping**: Full strain tensor ($\varepsilon_{xx}, \varepsilon_{yy}, \varepsilon_{xy}$) and rotation visualization.
- **Polished GUI**: A new tabbed interface with a collapsible sidebar for a better user experience.
- **Publication-Quality Plots**: Scalable vector maps, heatmaps with smart edge masking, and automatic scale bars.

## 🚀 New Features

### Visualization

- **Color-Coded Vectors**: Displacement vectors can now be colored by **angle** (using an HSV color wheel) or **magnitude**.
- **Smart Heatmaps**: Displacement magnitude heatmaps now use **Convex Hull Masking** to automatically hide edge artifacts where data is unreliable.
- **Statistics**: Added histograms for displacement magnitudes (with Gaussian fit) and polar plots for angle distribution.
- **Scale Bars**: Plots now automatically include scale bars if the pixel scale is known.

### User Interface

- **Tabbed Layout**: Results are organized into "Overview", "Color Vectors", "Statistics", and "Strain Analysis".
- **Responsive Design**: Images utilize a custom `ScalableImageLabel` widget to maintain aspect ratio and center alignment during window resizing.
- **Compact Sidebar**: The control panel has been optimized to maximize screen real estate for results (180px width).

### Core Algorithms

- **Strain Calculation**: Implemented numerical gradient-based strain tensor computation.
- **Edge Handling**: Added convex hull algorithms to cleaner visualizations.
- **Performance**: Linear interpolation replaces cubic for faster and artifact-free heatmap generation.

## 🐛 Bug Fixes

- Fixed a **Segmentation Fault** caused by infinite recursion in the image resizing logic.
- Resolved layout issues where long file paths would expand the sidebar uncontrollably.
- Eliminated "jagged edge" artifacts in heatmaps by switching to linear interpolation with nearest-neighbor boundary handling (later refined to masking).

## 📝 Documentation

- Added a comprehensive **[User Manual](docs/USER_MANUAL.md)**.
- Refactored `README.md` to serve as a streamlined project landing page.

## 🔧 Upgrade Instructions

No database migrations or config changes required. Simply pull the latest code and install dependencies:

```bash
pip install -r requirements.txt
python main.py
```
