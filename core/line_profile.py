"""Line profile analysis for displacement and strain data."""

from pathlib import Path
from typing import Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial import cKDTree


def compute_line_profile(
    points: np.ndarray,
    values: np.ndarray,
    start: Tuple[float, float],
    end: Tuple[float, float],
    num_samples: int = 100,
    search_radius: Optional[float] = None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute a line profile through scattered data.

    Args:
        points: (N, 2) array of data point positions (x, y).
        values: (N,) array of values at each point.
        start: (x, y) start point of line.
        end: (x, y) end point of line.
        num_samples: Number of samples along the line.
        search_radius: Radius for nearest-neighbor averaging. If None, uses
                       1/10 of the line length.

    Returns:
        Tuple of (distances, positions, sampled_values):
            - distances: 1D array of distances from start (length num_samples)
            - positions: (num_samples, 2) array of (x, y) positions along line
            - sampled_values: 1D array of interpolated values
    """
    start = np.array(start)
    end = np.array(end)
    line_vec = end - start
    line_length = np.linalg.norm(line_vec)

    if search_radius is None:
        search_radius = line_length / 10

    # Sample positions along line
    t = np.linspace(0, 1, num_samples)
    positions = start + np.outer(t, line_vec)
    distances = t * line_length

    # Build KD-tree for efficient neighbor search
    tree = cKDTree(points)

    sampled_values = np.zeros(num_samples)
    for i, pos in enumerate(positions):
        # Find all points within search_radius
        indices = tree.query_ball_point(pos, r=search_radius)
        if len(indices) == 0:
            # Fall back to nearest neighbor
            _, idx = tree.query(pos, k=1)
            sampled_values[i] = values[idx]
        else:
            # Distance-weighted average
            neighbor_points = points[indices]
            neighbor_values = values[indices]
            dists = np.linalg.norm(neighbor_points - pos, axis=1)
            # Inverse distance weighting (avoid division by zero)
            weights = 1.0 / (dists + 1e-10)
            sampled_values[i] = np.sum(weights * neighbor_values) / np.sum(weights)

    return distances, positions, sampled_values


def save_line_profile_plot(
    distances: np.ndarray,
    values: np.ndarray,
    path: Path,
    xlabel: str = "Distance (px)",
    ylabel: str = "Value",
    title: str = "Line Profile",
    nm_per_pixel: Optional[float] = None,
) -> None:
    """
    Save a line profile plot.

    Args:
        distances: 1D array of distances along the line.
        values: 1D array of values.
        path: Output file path.
        xlabel: X-axis label.
        ylabel: Y-axis label.
        title: Plot title.
        nm_per_pixel: If provided, converts distances to nm.
    """
    if nm_per_pixel is not None:
        distances = distances * nm_per_pixel
        xlabel = xlabel.replace("px", "nm")

    fig, ax = plt.subplots(figsize=(10, 4))

    ax.plot(distances, values, "b-", linewidth=1.5, marker=".", markersize=3, alpha=0.7)
    ax.fill_between(distances, values, alpha=0.2)

    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(title, fontsize=14)
    ax.grid(True, alpha=0.3)

    # Add statistics annotation
    stats_text = f"Mean: {np.mean(values):.3f}\nStd: {np.std(values):.3f}\nMax: {np.max(values):.3f}"
    ax.text(
        0.97, 0.97, stats_text, transform=ax.transAxes, fontsize=9,
        verticalalignment="top", horizontalalignment="right",
        bbox={"boxstyle": "round", "facecolor": "wheat", "alpha": 0.8}
    )

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def save_line_profile_on_image(
    image: np.ndarray,
    start: Tuple[float, float],
    end: Tuple[float, float],
    path: Path,
    line_color: str = "red",
    linewidth: float = 2,
) -> None:
    """
    Save image with line profile overlay.

    Args:
        image: 2D grayscale image.
        start: (x, y) start point.
        end: (x, y) end point.
        path: Output file path.
        line_color: Color of the line.
        linewidth: Width of the line.
    """
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.imshow(image, cmap="gray")

    ax.plot(
        [start[0], end[0]],
        [start[1], end[1]],
        color=line_color,
        linewidth=linewidth,
        marker="o",
        markersize=8,
    )

    # Add labels at start and end
    ax.annotate(
        "Start", start, textcoords="offset points", xytext=(10, 10),
        fontsize=10, color=line_color, fontweight="bold"
    )
    ax.annotate(
        "End", end, textcoords="offset points", xytext=(10, 10),
        fontsize=10, color=line_color, fontweight="bold"
    )

    ax.axis("off")

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def save_line_profile_csv(
    distances: np.ndarray,
    positions: np.ndarray,
    values: np.ndarray,
    path: Path,
    value_name: str = "value",
) -> None:
    """
    Save line profile data to CSV.

    Args:
        distances: 1D array of distances.
        positions: (N, 2) array of (x, y) positions.
        values: 1D array of values.
        path: Output file path.
        value_name: Name of the value column.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    header = f"distance,x,y,{value_name}"
    data = np.column_stack((distances, positions, values))
    np.savetxt(path, data, delimiter=",", header=header, comments="")
