"""
Command-line test runner for the Atomap pipeline.
Defaults match the example in ./data for easy IDE execution.
"""

import argparse
import os
from pathlib import Path
from typing import Optional

import numpy as np
import hyperspy.api as hs
from PIL import Image, ImageDraw
import tqdm
import sys
import matplotlib.pyplot as plt

# Disable tqdm notebook bars to avoid AttributeError when closing
os.environ.setdefault("TQDM_DISABLE", "1")
try:  # pragma: no cover - defensive patch
    import tqdm.notebook as tnb
    tnb.tqdm = tqdm.tqdm
except Exception:
    pass

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core import pipeline
from core import io_utils
from core import viz

DEFAULT_IMAGE = "data"
DEFAULT_OUT = "tests/output"


def _to_nm_per_px(scale: float, units: str) -> Optional[float]:
    """Convert axis scale+unit to nm/px if possible."""
    if scale is None:
        return None
    if not units:
        return None
    u = units.lower()
    if u.startswith("nm"):
        return scale
    if u in {"pm", "picometer", "picometre"}:
        return scale * 1e-3
    if u in {"µm", "um", "micrometer", "micrometre"}:
        return scale * 1e3
    if u in {"a", "å", "angstrom", "angström"}:
        return scale * 0.1
    return None


def get_metadata_hints(path: Path) -> tuple[Optional[float], bool]:
    """
    Try to infer nm_per_px and whether to invert from dm3 metadata + filename.
    Returns (nm_per_px, invert_flag).
    """
    nm_per_px = None
    invert = False
    meta_text = ""
    try:
        sig = hs.load(path, lazy=True)
        axes = getattr(sig.axes_manager, "signal_axes", sig.axes_manager)
        nm_vals = []
        for ax in axes:
            # Skip navigation axes if present
            if getattr(ax, "is_navigator", False):
                continue
            nm = _to_nm_per_px(getattr(ax, "scale", None), getattr(ax, "units", "") or "")
            if nm:
                nm_vals.append(nm)
        if nm_vals:
            nm_per_px = float(np.mean(nm_vals))
        meta_text = str(sig.metadata.as_dictionary()).upper()
    except Exception:
        meta_text = ""

    upper_name = path.name.upper()
    meta_upper = meta_text

    # Heuristics: DF-I/DFI indicates inverted dark field; BF/ABF often needs inversion; HAADF/ADF usually not.
    if any(k in upper_name for k in ["DF-I", "DFI", "DF_I"]):
        invert = True
    elif "INVERT" in meta_upper or "DF-I" in meta_upper:
        invert = True
    elif any(k in meta_upper for k in [" BF", "ABF", "BRIGHTFIELD", "BRIGHT FIELD"]):
        invert = True
    elif any(k in meta_upper for k in ["HAADF", "ADF", "DARKFIELD", "DARK FIELD"]):
        invert = False

    return nm_per_px, invert


def save_peaks_overlay(image: np.ndarray, peaks_a: np.ndarray, peaks_b: np.ndarray, path: Path, radius: int = 3):
    """Save an RGB image with detected peaks marked (A: lime, B: red)."""
    arr = image - np.nanmin(image)
    if np.nanmax(arr) > 0:
        arr = arr / np.nanmax(arr) * 255.0
    base = Image.fromarray(arr.astype(np.uint8)).convert("RGB")
    draw = ImageDraw.Draw(base)
    for x, y in peaks_a:
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), outline="lime", width=1)
    for x, y in peaks_b:
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), outline="red", width=1)
    base.save(path)


def save_displacement_arrows(
    image: np.ndarray,
    base_points: np.ndarray,
    dx: np.ndarray,
    dy: np.ndarray,
    path: Path,
    scale: Optional[float] = None,
    arrow_scale: Optional[float] = None,
):
    """Save an image with displacement arrows (base at ideal B positions, pointing to actual B)."""
    scale_factor = arrow_scale if arrow_scale else 1.0
    dx_draw = dx * scale_factor
    dy_draw = dy * scale_factor

    plt.figure(figsize=(6, 6))
    plt.imshow(image, cmap="gray")
    plt.quiver(
        base_points[:, 0],
        base_points[:, 1],
        dx_draw,
        dy_draw,
        color="yellow",
        angles="xy",
        scale_units="xy",
        scale=1,
        width=0.003,
        headwidth=3,
    )
    if scale:
        plt.title(f"Displacement arrows (red), scale: {scale} nm/px")
    else:
        plt.title(f"Displacement arrows (green) x{scale_factor:.2f}")
    plt.axis("off")
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()


def save_displacement_heatmap(image: np.ndarray, points: np.ndarray, magnitudes: np.ndarray, path: Path):
    """Plot interpolated displacement magnitude over grid (no image overlay)."""
    from scipy.interpolate import griddata

    h, w = image.shape
    grid_x, grid_y = np.mgrid[0:w:200j, 0:h:200j]  # 200x200 grid
    grid_mag = griddata(points, magnitudes, (grid_x, grid_y), method="cubic", fill_value=np.nan)

    plt.figure(figsize=(6, 6))
    im = plt.imshow(grid_mag.T, origin="lower", cmap="magma", extent=(0, w, 0, h))
    plt.colorbar(im, label="|displacement| (px)")
    plt.title("Displacement magnitude heatmap (interpolated)")
    plt.axis("off")
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()


def parse_args():
    parser = argparse.ArgumentParser(description="Run Atomap pipeline on a STEM image.")
    parser.add_argument("--image", default=DEFAULT_IMAGE, help="Input image path or directory (dm3/tif/jpg). If directory, all dm3 files are processed.")
    parser.add_argument("--output", default=DEFAULT_OUT, help="Output directory for results.")
    parser.add_argument("--sigma", type=float, default=1.0, help="Gaussian sigma for preprocessing.")
    parser.add_argument("--refine-sigma", type=float, default=1.0, help="Sigma for Gaussian refinement.")
    parser.add_argument("--separation", type=float, default=None, help="Lattice separation (px). If omitted, auto-estimate.")
    parser.add_argument("--threshold", type=float, default=None, help="Relative threshold for peak finding.")
    parser.add_argument("--nm-per-pixel", type=float, default=None, help="Scale factor to convert px to nm.")
    parser.add_argument("--arrow-scale", type=float, default=None, help="Scale factor to magnify displacement arrows (px). Default uses lattice separation.")
    return parser.parse_args()


def main():
    args = parse_args()

    input_path = Path(args.image)
    files = []
    if input_path.is_dir():
        files = sorted(input_path.glob("*.dm3"))
        if not files:
            raise FileNotFoundError(f"No dm3 files found in directory: {input_path}")
    elif input_path.is_file():
        files = [input_path]
    else:
        raise FileNotFoundError(f"Input path not found: {input_path}")

    out_root = Path(args.output)
    out_root.mkdir(parents=True, exist_ok=True)

    succeeded, failed = [], []
    for f in files:
        out_dir = out_root / f.stem
        out_dir.mkdir(parents=True, exist_ok=True)
        print(f"Processing {f} -> {out_dir}")

        auto_nm_per_px, auto_invert = get_metadata_hints(f)
        nm_per_px = args.nm_per_pixel if args.nm_per_pixel is not None else auto_nm_per_px
        invert_flag = auto_invert

        # Save raw and inverted preview (to verify automatic inversion on DF-I/BF)
        try:
            raw_img = io_utils.load_image(f)
            io_utils.save_png(raw_img, out_dir / "raw.png")
            if invert_flag:
                inv_img = raw_img.max() - raw_img
                io_utils.save_png(inv_img, out_dir / "raw_inverted.png")
        except Exception:
            pass

        try:
            result = pipeline.run_pipeline(
                image_path=str(f),
                gaussian_sigma=args.sigma,
                background_sigma=None,
                roi=None,
                separation=args.separation,
                threshold=args.threshold,
                refine_sigma=args.refine_sigma,
                nm_per_pixel=nm_per_px,
                invert=invert_flag,
                output_dir=out_dir,
            )

            io_utils.save_png(result.image, out_dir / "preprocessed.png")
            io_utils.save_csv(result.peaks_a, header="x,y", path=out_dir / "peaks_a.csv")
            io_utils.save_csv(result.peaks_b, header="x,y", path=out_dir / "peaks_b.csv")
            save_peaks_overlay(result.image, result.peaks_a, result.peaks_b, out_dir / "peaks_overlay.png")

            dx_px = result.displacement["dx"]
            dy_px = result.displacement["dy"]
            disp_px = np.column_stack((dx_px, dy_px))
            io_utils.save_csv(disp_px, header="dx,dy (pixels)", path=out_dir / "displacement.csv")
            viz.plot_displacement(dx_px.reshape(-1, 1), dy_px.reshape(-1, 1), save_path=out_dir / "displacement.png")

            # Arrow overlay: use ideal B as base, dx/dy as vectors
            save_displacement_arrows(
                result.image,
                result.ideal_b,
                dx_px,
                dy_px,
                out_dir / "displacement_arrows.png",
                scale=args.nm_per_pixel,
                arrow_scale=args.arrow_scale or result.separation,
            )

            # Heatmap of displacement magnitude at B positions
            mag_px = np.hypot(dx_px, dy_px)
            save_displacement_heatmap(result.image, result.peaks_b, mag_px, out_dir / "displacement_heatmap.png")

            if result.displacement.get("dx_nm") is not None:
                dx_nm = result.displacement["dx_nm"]
                dy_nm = result.displacement["dy_nm"]
                disp_nm = np.column_stack((dx_nm, dy_nm))
                io_utils.save_csv(disp_nm, header="dx,dy (nm)", path=out_dir / "displacement_nm.csv")

            succeeded.append(out_dir)
            print(f"Done: {out_dir.resolve()}")
        except Exception as exc:
            failed.append((f, exc))
            print(f"[WARN] Skip {f}: {exc}")
            continue

    print(f"\nSummary: {len(succeeded)} success, {len(failed)} skipped.")
    if failed:
        for f, exc in failed:
            print(f"  - {f}: {exc}")


if __name__ == "__main__":
    main()
