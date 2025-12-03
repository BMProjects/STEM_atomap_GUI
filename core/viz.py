from pathlib import Path
from typing import Optional

import matplotlib
matplotlib.use("Agg")  # ensure headless backend
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import griddata


def plot_heatmap(array: np.ndarray, title: str = "", cmap: str = "magma", save_path: Optional[Path] = None):
    fig, ax = plt.subplots(figsize=(5, 4))
    im = ax.imshow(array, cmap=cmap)
    ax.set_title(title)
    ax.axis("off")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return fig


def plot_displacement(dx: np.ndarray, dy: np.ndarray, title: str = "Displacement magnitude", cmap: str = "magma", save_path: Optional[Path] = None):
    mag = np.hypot(dx, dy)
    return plot_heatmap(mag, title=title, cmap=cmap, save_path=save_path)


def save_peaks_overlay(image: np.ndarray, peaks_a: np.ndarray, peaks_b: np.ndarray, path: Path, radius: int = 3):
    """Save an RGB image with detected peaks marked (A: lime, B: red) using PIL."""
    from PIL import Image, ImageDraw

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
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
    arrow_scale: float = 1.0,
    color: str = "yellow",
    scale_nm_per_px: Optional[float] = None,
):
    """Save an image with displacement arrows (base at ideal B positions)."""
    import matplotlib.pyplot as plt

    dx_draw = dx * arrow_scale
    dy_draw = dy * arrow_scale

    plt.figure(figsize=(6, 6))
    plt.imshow(image, cmap="gray")
    plt.quiver(
        base_points[:, 0],
        base_points[:, 1],
        dx_draw,
        dy_draw,
        color=color,
        angles="xy",
        scale_units="xy",
        scale=1,
        width=0.003,
        headwidth=3,
    )
    if scale_nm_per_px:
        plt.title(f"Displacement arrows, scale: {scale_nm_per_px} nm/px, arrow x{arrow_scale:.2f}")
    else:
        plt.title(f"Displacement arrows x{arrow_scale:.2f}")
    plt.axis("off")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()


def save_displacement_heatmap(image: np.ndarray, points: np.ndarray, magnitudes: np.ndarray, path: Path):
    """Plot interpolated displacement magnitude over grid (no image overlay)."""
    import matplotlib.pyplot as plt

    h, w = image.shape
    grid_x, grid_y = np.mgrid[0:w:200j, 0:h:200j]  # 200x200 grid
    grid_mag = griddata(points, magnitudes, (grid_x, grid_y), method="cubic", fill_value=np.nan)

    plt.figure(figsize=(6, 6))
    im = plt.imshow(grid_mag.T, origin="lower", cmap="magma", extent=(0, w, 0, h))
    plt.colorbar(im, label="|displacement| (px)")
    plt.title("Displacement magnitude heatmap (interpolated)")
    plt.axis("off")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()
