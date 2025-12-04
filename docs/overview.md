# STEM Atomap GUI – Design & Usage Overview (v0.1.1)

## 1. Requirements
- **Functionality**: Load STEM images (dm3 preferred), preprocess, detect A/B cation sublattices, compute B-site displacements relative to ideal centrosymmetric positions, visualize peaks/arrows/heatmap, export CSV/PNG, and provide a PySide6 GUI plus a CLI test script.
- **Inputs**: STEM images under `./data` (dm3, tif/jpg fallback). Optional: manual lattice separation (px), threshold, Gaussian sigmas, nm-per-pixel scale.
- **Outputs**: Per-image folder (`outputs/<stem>/` or `tests/output/<stem>/`) with `preprocessed.png`, peaks CSVs, overlays, displacement CSV/plots, heatmap, and optional nm CSV.
- **Non-functional**: Run offline; minimal dependencies; avoid GPU/JIT issues (numba disabled); logging to `log/app.log`; headless-safe plotting (Agg).

## 2. Overall Design
- **Layers**
  - `core/`: preprocessing, I/O, lattice building, metrics, visualization, pipeline orchestration.
  - `ui_qt/`: PySide6 main window with controls, preview pane, status bar, output viewers.
  - `tests/`: CLI runner for batch processing.
  - `assets/`, `outputs/`, `log/`, `VERSION`.
- **Data Flow (Pipeline)**
  1) Load image via HyperSpy (dm3) or PIL (others).
  2) Preprocess: optional ROI, background removal, Gaussian blur, optional inversion, normalize.
  3) Estimate lattice separation from FFT (or use provided value).
  4) Build A sublattice (peak find → zone axes) and derive ideal B positions (centers between A neighbors).
  5) Build/refine B sublattice and compute displacements `dx, dy = peaks_b - ideal_b`; magnitudes; optional nm conversion.
  6) Save standard artifacts: overlays, arrows (scaled), heatmap (interpolated magnitude), CSVs.
- **Automation Hints**
  - HyperSpy metadata parsed for nm/px (axes scale) and contrast mode hints.
  - Filename/metadata heuristics for inversion (DF-I/BF/ABF → invert; HAADF/ADF → no invert).

## 3. Detailed Design
- **core/io_utils.py**
  - `load_image`: dm3/dm4 via HyperSpy, else PIL; returns float64 array.
  - `save_png`, `save_csv`, `crop_roi`.
- **core/preprocess.py**
  - `preprocess_image`: ROI crop → optional inversion → optional background removal (Gaussian) → Gaussian smoothing → normalize to 0–1.
- **core/lattice.py**
  - `_estimate_separation_from_fft`: FFT-based dominant frequency to px separation.
  - `build_sublattices`: find A peaks (atomap), construct zone axes, derive ideal B (centers), build B sublattice; may raise if zone axes insufficient.
  - `compute_b_displacements`: returns dx, dy between detected B and ideal B.
- **core/pipeline.py**
  - `run_pipeline(...)`: orchestrates load → preprocess → separation → sublattices → displacement → save standard outputs (PNG/CSV/overlays). Accepts `invert`, `nm_per_pixel`.
  - Logging setup (`log/app.log`); disables numba JIT and tqdm notebook issues.
  - `PipelineResult`: carries images, peaks, displacements, paths.
- **core/viz.py**
  - `save_peaks_overlay`, `save_displacement_arrows` (yellow arrows, scalable), `save_displacement_heatmap` (interpolated magnitude, no overlay). Matplotlib Agg backend; PIL for overlays (no cv2).
- **ui_qt/main_window.py**
  - Left panel: file chooser, params (sigma, separation, threshold, refine sigma), scale input (nm/px), run button.
  - Right panel: 2×2 outputs (preprocessed/peaks, arrows, heatmap, previews). Status bar shows progress and output dir.
  - Loads overlays after run; logs errors.
- **tests/test_pipeline.py**
  - CLI arguments: `--image` (file or dir; dm3 batch), `--output`, `--sigma`, `--refine-sigma`, `--separation`, `--threshold`, `--nm-per-pixel`, `--arrow-scale`.
  - For each file: auto metadata hints (nm/px, invert), save `raw.png` and `raw_inverted.png` when inversion is suggested, then run pipeline, save artifacts and summary.

## 4. User Manual
### Install
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run GUI
```bash
python main.py
```
Steps: select image → set/confirm params (separation if known, nm/px if known) → run. Preview updates; outputs saved to `outputs/<filename-stem>/`. Status bar shows progress; logs in `log/app.log`.

### Run CLI Tests
```bash
python tests/test_pipeline.py
# optional examples:
# python tests/test_pipeline.py --image data/250525\ 154446\ STEM\ 5.1Mx\ HAADF\ c.dm3 --separation 20 --nm-per-pixel 0.02
# python tests/test_pipeline.py --image data --output tests/output --arrow-scale 30
```
Outputs per file under `tests/output/<stem>/`: `raw.png`, optional `raw_inverted.png`, `preprocessed.png`, `peaks_a/b.csv`, `peaks_overlay.png`, `displacement.csv` (px, optional nm), `displacement_arrows.png`, `displacement_heatmap.png`.

### Inputs & Parameters
- **Image**: dm3 preferred (metadata used); others (tif/jpg) supported.
- **Separation (px)**: provide if automatic FFT estimate fails or for high magnification.
- **Threshold**: peak-finding relative threshold; lower to pick weaker peaks.
- **Sigma / refine-sigma**: Gaussian smoothing for preprocessing and refinement.
- **nm-per-pixel**: use metadata if present; can override manually for accurate nm outputs.
- **Invert**: auto-inferred (DF-I/BF/ABF) but can be overridden by editing run parameters if needed.

### Outputs
- `raw.png` / `raw_inverted.png` (tests only): sanity check for contrast.
- `preprocessed.png`: filtered/inverted/normalized image used for detection.
- `peaks_a.csv`, `peaks_b.csv`, `peaks_overlay.png`: detected A/B peaks.
- `displacement.csv` (px) and optional `displacement_nm.csv`.
- `displacement_arrows.png`: yellow arrows from ideal B to detected B (scaled).
- `displacement_heatmap.png`: interpolated |displacement| magnitude map.

### Troubleshooting
- “Not enough zone axes…”: provide `--separation`, adjust `--threshold` lower, ensure correct inversion, or use a larger ROI with clearer lattice.
- Empty heatmap/arrows: verify B peaks detected; check `peaks_overlay.png`.
- Metadata issues: pass `--nm-per-pixel` manually; if contrast is wrong, manually invert via params.

## 5. Extensibility Notes
- Strain calculation placeholder in `pipeline.py` (needs atomap strain support).
- For robustness: expose more atomap parameters (nearest neighbors, atom_plane_tolerance), add a manual invert flag to CLI/GUI, add batch UI.
- Consider reading detector/mode metadata more comprehensively and adding a per-file debug dump for failures.

## 6. Testing Plan (current focus)
- **GUI sanity**: load a single HAADF dm3, set separation/nm-per-pixel manually, run and verify previews, status updates, output folder artifacts, and log entries.
- **CLI single**: `python tests/test_pipeline.py --image data/<file>.dm3 --output tests/output_single --arrow-scale 30 --nm-per-pixel 0.02`; check full outputs, no exceptions.
- **Metadata/inversion**: dm3 with scale in metadata (nm-per-pixel omitted) → verify displacement_nm.csv; DF-I/BF files → inspect `raw.png` vs `raw_inverted.png`, confirm overlay correctness.
- **Batch & robustness**: `python tests/test_pipeline.py --image data --output tests/output_batch`; ensure summary counts, failed files skipped without blocking others; log contains no unhandled errors.
- **Parameter sensitivity**: compare auto vs manual separation; tweak threshold up/down to see B detection stability; adjust arrow_scale for readability.
- **Visual checks**: peaks_overlay (colors/positions), displacement_arrows (direction/length), displacement_heatmap (coverage, no large NaN patches).
- **Edge cases**: FFT/very sparse images → graceful skip/error; non-dm3 (tif/jpg) load; invalid path handling.
- **Performance**: observe runtime on medium images, ensure no hangs/low-CPU stalls; headless CLI uses Agg backend without GUI blocking.
