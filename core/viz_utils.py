"""Visualization utility functions for scale bars, colorbars, and color mappings."""

from pathlib import Path
from typing import Literal, Optional, Tuple

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.cm import ScalarMappable
import numpy as np


def angle_to_hsv_rgb(angles: np.ndarray) -> np.ndarray:
    """
    Convert displacement angles to RGB colors using HSV color wheel.

    Args:
        angles: Array of angles in radians, range [-π, π].

    Returns:
        RGB array of shape (..., 3) with values in [0, 1].
    """
    # Normalize angle from [-π, π] to [0, 1] for Hue
    hue = (angles + np.pi) / (2 * np.pi)
    hue = np.clip(hue, 0, 1)

    # Full saturation and value for vivid colors
    ones = np.ones_like(hue)
    hsv = np.stack([hue, ones, ones], axis=-1)

    # Convert HSV to RGB
    return mcolors.hsv_to_rgb(hsv)


def magnitude_to_rgb(
    magnitudes: np.ndarray,
    cmap: str = "magma",
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
) -> Tuple[np.ndarray, ScalarMappable]:
    """
    Convert displacement magnitudes to RGB colors using a colormap.

    Args:
        magnitudes: Array of magnitude values.
        cmap: Matplotlib colormap name.
        vmin: Minimum value for normalization (default: min of magnitudes).
        vmax: Maximum value for normalization (default: max of magnitudes).

    Returns:
        Tuple of (RGB array shape (..., 3), ScalarMappable for colorbar).
    """
    if vmin is None:
        vmin = np.nanmin(magnitudes)
    if vmax is None:
        vmax = np.nanmax(magnitudes)

    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
    colormap = plt.get_cmap(cmap)
    mappable = ScalarMappable(norm=norm, cmap=colormap)

    # Get RGBA and extract RGB
    rgba = mappable.to_rgba(magnitudes)
    rgb = rgba[..., :3]

    return rgb, mappable


def add_scale_bar(
    ax: Axes,
    nm_per_pixel: float,
    image_width_px: int,
    bar_length_nm: Optional[float] = None,
    location: Literal["lower right", "lower left", "upper right", "upper left"] = "lower right",
    color: str = "white",
    font_size: int = 10,
    box_alpha: float = 0.5,
) -> None:
    """
    Add a scale bar to a matplotlib axes.

    Args:
        ax: Matplotlib axes.
        nm_per_pixel: Scale factor (nm per pixel).
        image_width_px: Image width in pixels.
        bar_length_nm: Desired scale bar length in nm (auto-calculated if None).
        location: Position of scale bar.
        color: Bar and text color.
        font_size: Font size for label.
        box_alpha: Background box transparency.
    """
    image_width_nm = image_width_px * nm_per_pixel

    # Auto-select a nice round bar length (~10-20% of image width)
    if bar_length_nm is None:
        target_nm = image_width_nm * 0.15
        # Round to nice values: 1, 2, 5, 10, 20, 50, 100, ...
        magnitude = 10 ** np.floor(np.log10(target_nm))
        for nice in [1, 2, 5, 10]:
            if nice * magnitude >= target_nm * 0.8:
                bar_length_nm = nice * magnitude
                break
        else:
            bar_length_nm = 10 * magnitude

    bar_length_px = bar_length_nm / nm_per_pixel

    # Calculate position based on location
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    margin = 0.05

    if "right" in location:
        x_start = xlim[1] - margin * (xlim[1] - xlim[0]) - bar_length_px
    else:
        x_start = xlim[0] + margin * (xlim[1] - xlim[0])

    if "lower" in location:
        y_pos = ylim[1] - margin * (ylim[1] - ylim[0])  # Note: y-axis may be inverted
    else:
        y_pos = ylim[0] + margin * (ylim[1] - ylim[0])

    # Draw bar
    bar = mpatches.FancyBboxPatch(
        (x_start, y_pos - 3),
        bar_length_px,
        6,
        boxstyle="square,pad=0",
        facecolor=color,
        edgecolor="none",
    )
    ax.add_patch(bar)

    # Format label (remove trailing zeros)
    if bar_length_nm >= 1:
        label = f"{bar_length_nm:.0f} nm"
    else:
        label = f"{bar_length_nm * 1000:.0f} pm"

    ax.text(
        x_start + bar_length_px / 2,
        y_pos - 10,
        label,
        ha="center",
        va="top",
        color=color,
        fontsize=font_size,
        fontweight="bold",
        bbox={"facecolor": "black", "alpha": box_alpha, "edgecolor": "none", "pad": 2},
    )


def add_angle_colorwheel(
    fig: Figure,
    position: Tuple[float, float, float, float] = (0.85, 0.15, 0.1, 0.1),
) -> None:
    """
    Add a circular HSV color wheel legend for angle-coded vectors.

    Args:
        fig: Matplotlib figure.
        position: (left, bottom, width, height) in figure coordinates.
    """
    ax_wheel = fig.add_axes(position, projection="polar")
    ax_wheel.set_theta_zero_location("E")  # 0° at right (East)

    # Create color wheel
    theta = np.linspace(0, 2 * np.pi, 256)
    radii = np.linspace(0.5, 1.0, 2)
    theta_grid, r_grid = np.meshgrid(theta, radii)

    # Map theta to hue
    colors = angle_to_hsv_rgb(theta_grid - np.pi)

    ax_wheel.pcolormesh(theta_grid, r_grid, theta_grid, color=colors.reshape(-1, 3), shading="auto")
    ax_wheel.set_yticks([])
    ax_wheel.set_xticks([0, np.pi / 2, np.pi, 3 * np.pi / 2])
    ax_wheel.set_xticklabels(["0°", "90°", "±180°", "-90°"], fontsize=6, color="white")
    ax_wheel.tick_params(colors="white", pad=1)
    ax_wheel.set_facecolor("black")


def create_convex_hull_mask(
    points: np.ndarray,
    grid_shape: Tuple[int, int],
    grid_extent: Tuple[float, float, float, float],
    shrink_margin: float = 0.05,
) -> np.ndarray:
    """
    Create a binary mask from the convex hull of data points.

    This masks out regions outside the convex hull of detected atoms,
    with an optional inward margin to exclude edge artifacts.

    Args:
        points: (N, 2) array of (x, y) data point positions.
        grid_shape: (rows, cols) shape of the output mask grid.
        grid_extent: (x_min, x_max, y_min, y_max) extent of the grid.
        shrink_margin: Fraction of hull size to shrink inward (0-1).
                       0 = no shrink, 0.05 = 5% shrink on each side.

    Returns:
        Boolean mask array of shape grid_shape. True = inside valid region.
    """
    from scipy.spatial import ConvexHull, Delaunay

    if len(points) < 4:
        # Not enough points for hull, return all True
        return np.ones(grid_shape, dtype=bool)

    try:
        hull = ConvexHull(points)
    except Exception:
        return np.ones(grid_shape, dtype=bool)

    # Get hull vertices
    hull_points = points[hull.vertices]

    # Shrink hull toward centroid
    if shrink_margin > 0:
        centroid = np.mean(hull_points, axis=0)
        hull_points = centroid + (1 - shrink_margin) * (hull_points - centroid)

    # Create grid coordinates
    x_min, x_max, y_min, y_max = grid_extent
    rows, cols = grid_shape
    x_coords = np.linspace(x_min, x_max, cols)
    y_coords = np.linspace(y_min, y_max, rows)
    grid_x, grid_y = np.meshgrid(x_coords, y_coords)
    grid_points = np.column_stack([grid_x.ravel(), grid_y.ravel()])

    # Check which grid points are inside the shrunk hull
    try:
        delaunay = Delaunay(hull_points)
        inside = delaunay.find_simplex(grid_points) >= 0
    except Exception:
        return np.ones(grid_shape, dtype=bool)

    mask = inside.reshape(grid_shape)
    return mask


def get_valid_data_bounds(
    points: np.ndarray,
    margin_fraction: float = 0.1,
) -> Tuple[float, float, float, float]:
    """
    Get bounding box of valid data region with margin removed.

    Args:
        points: (N, 2) array of (x, y) data point positions.
        margin_fraction: Fraction of range to remove from each edge.

    Returns:
        (x_min, x_max, y_min, y_max) of the cropped bounds.
    """
    x_min, y_min = points.min(axis=0)
    x_max, y_max = points.max(axis=0)

    x_range = x_max - x_min
    y_range = y_max - y_min

    x_margin = x_range * margin_fraction
    y_margin = y_range * margin_fraction

    return (
        x_min + x_margin,
        x_max - x_margin,
        y_min + y_margin,
        y_max - y_margin,
    )

