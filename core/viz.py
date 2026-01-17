from pathlib import Path
from typing import Literal, Optional

import matplotlib
matplotlib.use("Agg")  # ensure headless backend
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import griddata

from . import viz_utils


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
    """Plot interpolated displacement magnitude over grid with convex hull masking."""
    import matplotlib.pyplot as plt

    h, w = image.shape
    grid_size = 200
    
    # Create interpolation grid
    grid_x, grid_y = np.mgrid[0:w:complex(0, grid_size), 0:h:complex(0, grid_size)]
    
    # Use linear interpolation (no edge filling)
    grid_mag = griddata(points, magnitudes, (grid_x, grid_y), method="linear", fill_value=np.nan)
    
    # Apply convex hull mask with shrink margin to exclude edge artifacts
    mask = viz_utils.create_convex_hull_mask(
        points,
        grid_shape=(grid_size, grid_size),
        grid_extent=(0, w, 0, h),
        shrink_margin=0.10,  # 10% shrink from convex hull
    )
    grid_mag[~mask.T] = np.nan  # Transpose to match grid orientation

    plt.figure(figsize=(6, 6))
    im = plt.imshow(grid_mag.T, origin="lower", cmap="magma", extent=(0, w, 0, h))
    plt.colorbar(im, label="|displacement| (px)")
    plt.title("Displacement magnitude heatmap")
    plt.axis("off")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()


def save_displacement_arrows_colored(
    image: np.ndarray,
    base_points: np.ndarray,
    dx: np.ndarray,
    dy: np.ndarray,
    path: Path,
    color_mode: Literal["angle", "magnitude"] = "angle",
    arrow_scale: float = 1.0,
    nm_per_pixel: Optional[float] = None,
    cmap: str = "magma",
) -> None:
    """
    Save displacement arrows with color encoding by angle (HSV wheel) or magnitude.

    Args:
        image: Background grayscale image.
        base_points: (N, 2) array of arrow base positions (x, y).
        dx: (N,) array of x-displacements.
        dy: (N,) array of y-displacements.
        path: Output file path.
        color_mode: "angle" for HSV color wheel, "magnitude" for colormap.
        arrow_scale: Multiplier for arrow length visualization.
        nm_per_pixel: If provided, adds a scale bar.
        cmap: Colormap for magnitude mode (default: magma).
    """
    dx_draw = dx * arrow_scale
    dy_draw = dy * arrow_scale

    # Calculate colors based on mode
    if color_mode == "angle":
        angles = np.arctan2(dy, dx)  # Note: dy first for standard math convention
        colors = viz_utils.angle_to_hsv_rgb(angles)
    else:  # magnitude
        magnitudes = np.hypot(dx, dy)
        colors, mappable = viz_utils.magnitude_to_rgb(magnitudes, cmap=cmap)

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.imshow(image, cmap="gray")

    # Draw arrows one by one with individual colors
    for i in range(len(base_points)):
        ax.quiver(
            base_points[i, 0],
            base_points[i, 1],
            dx_draw[i],
            dy_draw[i],
            color=colors[i],
            angles="xy",
            scale_units="xy",
            scale=1,
            width=0.004,
            headwidth=3,
            headlength=4,
        )

    # Add legend/colorbar
    if color_mode == "angle":
        viz_utils.add_angle_colorwheel(fig, position=(0.82, 0.12, 0.12, 0.12))
        title = f"Displacement direction (HSV) ×{arrow_scale:.1f}"
    else:
        cbar = fig.colorbar(mappable, ax=ax, fraction=0.046, pad=0.04)
        unit = "nm" if nm_per_pixel else "px"
        cbar.set_label(f"|displacement| ({unit})", fontsize=10)
        title = f"Displacement magnitude ×{arrow_scale:.1f}"

    # Add scale bar if nm_per_pixel provided
    if nm_per_pixel is not None:
        viz_utils.add_scale_bar(ax, nm_per_pixel, image.shape[1])

    ax.set_title(title, fontsize=12)
    ax.axis("off")

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="black")
    plt.close(fig)


def save_strain_maps(
    strain_data: dict,
    image_shape: tuple,
    path_prefix: Path,
    nm_per_pixel: Optional[float] = None,
) -> None:
    """
    Save strain tensor component maps (εxx, εyy, εxy, rotation) with convex hull masking.

    Args:
        strain_data: Dictionary from compute_strain_from_displacement.
        image_shape: (height, width) of original image.
        path_prefix: Path prefix for output files (e.g., "outputs/sample/strain").
        nm_per_pixel: Scale factor for axis labels.
    """
    path_prefix = Path(path_prefix)
    path_prefix.parent.mkdir(parents=True, exist_ok=True)

    h, w = image_shape

    components = [
        ("exx", "ε$_{xx}$ (∂u/∂x)", "RdBu_r"),
        ("eyy", "ε$_{yy}$ (∂v/∂y)", "RdBu_r"),
        ("exy", "ε$_{xy}$ (shear)", "PuOr_r"),
        ("rotation_deg", "Rotation (°)", "PiYG"),
    ]

    # Create convex hull mask if source points are available
    mask = None
    if "source_points" in strain_data and "exx" in strain_data:
        grid_shape = strain_data["exx"].shape
        mask = viz_utils.create_convex_hull_mask(
            strain_data["source_points"],
            grid_shape=grid_shape,
            grid_extent=(0, w, 0, h),
            shrink_margin=0.10,
        )

    for key, title, cmap in components:
        if key not in strain_data:
            continue

        data = strain_data[key].copy()
        if data is None or np.all(np.isnan(data)):
            continue

        # Apply mask
        if mask is not None:
            data[~mask] = np.nan

        fig, ax = plt.subplots(figsize=(7, 6))

        # Symmetric colormap centered at zero
        vmax = np.nanpercentile(np.abs(data), 98)
        vmin = -vmax

        im = ax.imshow(
            data.T,  # Transpose for correct orientation
            origin="lower",
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            extent=(0, w, 0, h),
        )

        cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        if key == "rotation_deg":
            cbar.set_label("Rotation (degrees)", fontsize=10)
        else:
            cbar.set_label("Strain (dimensionless)", fontsize=10)

        ax.set_title(title, fontsize=14)
        ax.axis("off")

        # Add scale bar if available
        if nm_per_pixel is not None:
            viz_utils.add_scale_bar(ax, nm_per_pixel, w)

        out_path = path_prefix.parent / f"{path_prefix.stem}_{key}.png"
        fig.savefig(out_path, dpi=300, bbox_inches="tight", facecolor="white")
        plt.close(fig)

    # Combined 2x2 figure
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes = axes.flatten()

    for idx, (key, title, cmap) in enumerate(components):
        if key not in strain_data:
            continue

        data = strain_data[key].copy()
        ax = axes[idx]

        # Apply mask
        if mask is not None:
            data[~mask] = np.nan

        vmax = np.nanpercentile(np.abs(data), 98)
        vmin = -vmax

        im = ax.imshow(
            data.T, origin="lower", cmap=cmap, vmin=vmin, vmax=vmax, extent=(0, w, 0, h)
        )
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        ax.set_title(title, fontsize=12)
        ax.axis("off")

    fig.suptitle("Strain Tensor Analysis", fontsize=16, y=0.98)
    fig.tight_layout()
    fig.savefig(path_prefix.parent / f"{path_prefix.stem}_combined.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

