"""
Command-line test runner for the Atomap pipeline.
Defaults match the example in ./data for easy IDE execution.
"""

import argparse
import os
from pathlib import Path
from typing import Optional

import numpy as np
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

DEFAULT_IMAGE = "data/250525 154446 STEM 5.1Mx HAADF c.dm3"
DEFAULT_OUT = "tests/output"


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
    parser.add_argument("--image", default=DEFAULT_IMAGE, help="Input image path (dm3/tif/jpg).")
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
    if not input_path.exists():
        raise FileNotFoundError(f"Sample image not found: {input_path}")

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    result = pipeline.run_pipeline(
        image_path=str(input_path),
        gaussian_sigma=args.sigma,
        background_sigma=None,
        roi=None,
        separation=args.separation,
        threshold=args.threshold,
        refine_sigma=args.refine_sigma,
        nm_per_pixel=args.nm_per_pixel,
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

    print(f"Done. Outputs saved to: {out_dir.resolve()}")


if __name__ == "__main__":
    main()
