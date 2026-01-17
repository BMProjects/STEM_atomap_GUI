"""Statistical analysis and visualization for displacement data."""

from pathlib import Path
from typing import Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats


def compute_statistics(
    dx: np.ndarray,
    dy: np.ndarray,
    nm_per_pixel: Optional[float] = None,
) -> dict:
    """
    Compute displacement statistics.

    Args:
        dx: X-displacement array.
        dy: Y-displacement array.
        nm_per_pixel: Scale factor for physical units.

    Returns:
        Dictionary with mean, std, min, max for magnitude and angles.
    """
    magnitudes = np.hypot(dx, dy)
    angles = np.arctan2(dy, dx)  # radians, range [-π, π]
    angles_deg = np.degrees(angles)

    result = {
        "count": len(magnitudes),
        "magnitude_mean": float(np.mean(magnitudes)),
        "magnitude_std": float(np.std(magnitudes)),
        "magnitude_min": float(np.min(magnitudes)),
        "magnitude_max": float(np.max(magnitudes)),
        "magnitude_median": float(np.median(magnitudes)),
        "angle_mean_deg": float(np.degrees(np.arctan2(np.mean(dy), np.mean(dx)))),
        "angle_circular_std_deg": float(np.degrees(np.sqrt(-2 * np.log(np.abs(np.mean(np.exp(1j * angles))))))),
    }

    if nm_per_pixel is not None:
        result["magnitude_mean_nm"] = result["magnitude_mean"] * nm_per_pixel
        result["magnitude_std_nm"] = result["magnitude_std"] * nm_per_pixel
        result["magnitude_min_nm"] = result["magnitude_min"] * nm_per_pixel
        result["magnitude_max_nm"] = result["magnitude_max"] * nm_per_pixel

    return result


def save_magnitude_histogram(
    magnitudes: np.ndarray,
    path: Path,
    nm_per_pixel: Optional[float] = None,
    bins: int = 50,
    fit_gaussian: bool = True,
) -> None:
    """
    Save displacement magnitude histogram.

    Args:
        magnitudes: Array of displacement magnitudes.
        path: Output file path.
        nm_per_pixel: Scale for physical units (nm).
        bins: Number of histogram bins.
        fit_gaussian: Whether to overlay a Gaussian fit.
    """
    unit = "nm" if nm_per_pixel else "px"
    data = magnitudes * nm_per_pixel if nm_per_pixel else magnitudes

    fig, ax = plt.subplots(figsize=(8, 5))

    # Histogram
    n, bin_edges, patches = ax.hist(
        data, bins=bins, density=True, alpha=0.7, color="steelblue", edgecolor="white"
    )

    # Gaussian fit
    if fit_gaussian and len(data) > 10:
        mu, std = stats.norm.fit(data)
        x_fit = np.linspace(data.min(), data.max(), 200)
        y_fit = stats.norm.pdf(x_fit, mu, std)
        ax.plot(x_fit, y_fit, "r-", linewidth=2, label=f"Gaussian: μ={mu:.3f}, σ={std:.3f}")
        ax.legend(loc="upper right")

    ax.set_xlabel(f"|Displacement| ({unit})", fontsize=12)
    ax.set_ylabel("Probability Density", fontsize=12)
    ax.set_title("Displacement Magnitude Distribution", fontsize=14)

    # Statistics annotation
    stats_text = f"N = {len(data)}\nMean = {np.mean(data):.3f} {unit}\nStd = {np.std(data):.3f} {unit}"
    ax.text(
        0.97, 0.75, stats_text, transform=ax.transAxes, fontsize=10,
        verticalalignment="top", horizontalalignment="right",
        bbox={"boxstyle": "round", "facecolor": "wheat", "alpha": 0.8}
    )

    ax.grid(True, alpha=0.3)

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def save_angle_polar_histogram(
    dx: np.ndarray,
    dy: np.ndarray,
    path: Path,
    bins: int = 36,
) -> None:
    """
    Save polar histogram of displacement angles.

    Args:
        dx: X-displacement array.
        dy: Y-displacement array.
        path: Output file path.
        bins: Number of angular bins (default 36 = 10° each).
    """
    angles = np.arctan2(dy, dx)  # radians

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={"projection": "polar"})

    # Histogram
    counts, bin_edges = np.histogram(angles, bins=bins, range=(-np.pi, np.pi))
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    bin_width = 2 * np.pi / bins

    # Color by angle using HSV
    from . import viz_utils
    colors = viz_utils.angle_to_hsv_rgb(bin_centers)

    bars = ax.bar(
        bin_centers, counts, width=bin_width * 0.9, bottom=0,
        color=colors, edgecolor="white", linewidth=0.5, alpha=0.85
    )

    # Formatting
    ax.set_theta_zero_location("E")  # 0° at East (right)
    ax.set_theta_direction(1)  # Counter-clockwise
    ax.set_xticks([0, np.pi/4, np.pi/2, 3*np.pi/4, np.pi, -3*np.pi/4, -np.pi/2, -np.pi/4])
    ax.set_xticklabels(["0°", "45°", "90°", "135°", "±180°", "-135°", "-90°", "-45°"])

    ax.set_title("Displacement Direction Distribution", fontsize=14, pad=20)

    # Add mean direction arrow
    mean_angle = np.arctan2(np.mean(dy), np.mean(dx))
    mean_mag = np.max(counts) * 0.8
    ax.annotate(
        "", xy=(mean_angle, mean_mag), xytext=(mean_angle, 0),
        arrowprops={"arrowstyle": "->", "color": "black", "lw": 2}
    )
    ax.text(
        mean_angle, mean_mag * 1.1, f"Mean: {np.degrees(mean_angle):.1f}°",
        ha="center", fontsize=10, fontweight="bold"
    )

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def save_statistics_summary(
    stats_dict: dict,
    path: Path,
) -> None:
    """Save statistics to a text file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = ["Displacement Statistics Summary", "=" * 40, ""]
    for key, value in stats_dict.items():
        if isinstance(value, float):
            lines.append(f"{key}: {value:.6f}")
        else:
            lines.append(f"{key}: {value}")

    path.write_text("\n".join(lines))
