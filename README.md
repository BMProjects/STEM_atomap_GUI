# STEM + Atomap GUI

Atomap-based STEM atomic position & displacement analysis with a PySide6 GUI. Core logic in `core/`, GUI in `ui_qt/`, CLI tests in `tests/`. Default input data directory: `./data`.

## Features
- Load STEM/HAADF 2D images (dm3/dm4/tif/jpg), optional scale (nm/px).
- Preprocess: Gaussian smoothing (tunable), normalization.
- Lattice estimation: FFT for separation, build A sublattice, derive ideal B positions from neighboring centers.
- Refinement: refine A/B sublattices to get actual B positions.
- Displacement: compute B vs ideal center vectors (dx, dy), optional nm; save arrows and interpolated heatmap.
- Outputs: per-image folder `outputs/<image-name>/` containing preprocessed image, A/B coords, overlays, displacement CSV/arrows/heatmap; logs in `log/app.log`.
- GUI: preview, parameter & scale inputs, status bar, A/B overlay, displacement arrows, heatmap.

## Structure
- `main.py`: Qt app entry.
- `config.py`: default params.
- `core/`: preprocessing, sublattices, displacement, visualization helpers.
- `ui_qt/`: PySide6 GUI.
- `tests/`: CLI test script and default output dir.
- `log/`: runtime logs.
- `outputs/`: default outputs (per input filename).
- `VERSION`: current version (0.1.1).

## Install
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run GUI
```bash
python main.py
```
Steps: choose image → set params/scale → run. GUI shows overlays/arrows/heatmap; status bar shows output dir; logs in `log/app.log`.

## CLI Test
```bash
python tests/test_pipeline.py
# optional:
# --image data/xxx.dm3 --output tests/output --nm-per-pixel 0.02 --arrow-scale 50
```
Outputs: `preprocessed.png`, `peaks_a/b.csv`, `peaks_overlay.png`, `displacement.csv` (px, optional nm), `displacement_arrows.png`, `displacement_heatmap.png`.

## Algorithm
1) Preprocess (Gaussian + normalize).  
2) FFT estimate separation (or manual).  
3) A sublattice via peak detection + zone axes.  
4) Ideal B from neighbor centers; build/refine B sublattice.  
5) Displacement `dx, dy = peaks_b - ideal_b`, magnitude `|d|`, optional nm.  
6) Visualization: A/B overlay, arrows (scalable), interpolated heatmap; saved to `outputs/<image-name>/`.

## Todo / Status
- Done:
  - PySide6 GUI with preview, status bar, scale input; 16:10 layout.
  - Atomap-based pipeline: preprocess, A/B detection, displacement computation, overlays/arrows/heatmap.
  - Metadata/filename hints for nm/px and auto inversion; batch CLI runner with raw/inverted previews.
  - Logging to `log/app.log`; standard outputs per image under `outputs/` or `tests/output/`.
  - Docs (`docs/overview.md`) and reference added; version bumped to 0.1.1.
- Next / Improve:
  - Expose manual invert flag in CLI/GUI to override heuristics.
  - More robust zone-axis detection tuning for high-mag/low-SNR images.
  - Optional strain mapping when atomap strain utilities are available.
  - Richer metadata parsing (detector/mode) and per-file debug dumps for failures.
  - Batch UI controls and progress reporting for multiple files.

## Reference
Weishen Liu, Bo Fu, Jingji Zhang, Xiang Ma, Yuming Mao, Quan Zong, Zhejie Zhu, Haoran Yuan, Yun Zhou, Wangfeng Bai,  
“Exceptional capacitive energy storage in CaTiO3-based ceramics featuring laminate nanodomains,” Chemical Engineering Journal,  
512 (2025) 162477. https://doi.org/10.1016/j.cej.2025.162477
