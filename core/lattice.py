from typing import Optional, Tuple, List

import atomap.api as am
from atomap.atom_lattice import Atom_Lattice
import atomap.analysis_tools as an_tools
import hyperspy.api as hs
import numpy as np
from scipy.spatial import cKDTree


def _estimate_separation_from_fft(image: np.ndarray, num_peaks: int = 6, min_radius: int = 5) -> Optional[float]:
    """
    Crude spacing estimate from FFT peak distances. Returns average real-space period in pixels.
    """
    f = np.fft.fftshift(np.fft.fft2(image))
    mag = np.abs(f)
    h, w = mag.shape
    cy, cx = h // 2, w // 2

    # Suppress center to avoid DC
    yy, xx = np.ogrid[:h, :w]
    mask = (yy - cy) ** 2 + (xx - cx) ** 2 <= min_radius**2
    mag_masked = mag.copy()
    mag_masked[mask] = 0

    flat_indices = np.argpartition(mag_masked.ravel(), -num_peaks)[-num_peaks:]
    coords = np.column_stack(np.unravel_index(flat_indices, mag_masked.shape))
    distances = np.linalg.norm(coords - np.array([[cy, cx]]), axis=1)
    distances = distances[distances > 0]
    if len(distances) == 0:
        return None

    # Real-space period ~ image_size / freq_distance
    periods = []
    for d in distances:
        periods.append(h / d)
        periods.append(w / d)
    return float(np.mean(periods)) if periods else None


def build_atom_lattice(
    image: np.ndarray,
    separation: Optional[float] = None,
    threshold: Optional[float] = None,
    refine_sigma: float = 1.0,
) -> Tuple[Atom_Lattice, np.ndarray, float]:
    """
    Detect atoms, build Atom_Lattice, and refine positions/lattice vectors.
    Returns (lattice, peaks, used_separation).
    """
    # Ensure plain contiguous numpy array then wrap as HyperSpy Signal2D
    image = np.array(image, dtype=np.float64, copy=False, order="C")
    signal = hs.signals.Signal2D(image)

    sep = separation
    if sep is None:
        sep = _estimate_separation_from_fft(image)
    if sep is None or sep <= 0:
        raise ValueError("Failed to estimate lattice separation; please provide separation in pixels.")

    peaks = am.get_atom_positions(signal, separation=sep, threshold_rel=threshold)
    lattice = am.make_atom_lattice_from_image(signal, pixel_separation=sep)
    if hasattr(lattice, "refine_atom_positions"):
        lattice.refine_atom_positions(image, sigma=refine_sigma)
    if hasattr(lattice, "refine_lattice_vectors"):
        lattice.refine_lattice_vectors()
    return lattice, peaks, sep


def build_sublattices(
    image: np.ndarray,
    separation: float,
    threshold: Optional[float] = None,
    refine_sigma: float = 1.0,
) -> Tuple[am.Sublattice, am.Sublattice, np.ndarray]:
    """
    Build A/B sublattices: A from peak finding, B from middle positions between zone axes planes.
    Returns (sublattice_A, sublattice_B, ideal_B_positions).
    """
    image = np.array(image, dtype=np.float64, copy=False, order="C")
    signal = hs.signals.Signal2D(image)

    peaks_a = am.get_atom_positions(signal, separation=separation, threshold_rel=threshold)
    sub_a = am.Sublattice(peaks_a, signal)
    sub_a.construct_zone_axes()

    if len(sub_a.zones_axis_average_distances) < 2:
        raise ValueError("Not enough zone axes detected to build B sublattice")

    za0 = sub_a.zones_axis_average_distances[0]
    za1 = sub_a.zones_axis_average_distances[1]

    # Ideal B positions as middle points between four A neighbors
    ideal_b_positions = an_tools.get_middle_position_list(sub_a, za0, za1)
    sub_b = am.Sublattice(ideal_b_positions, signal)
    sub_b.find_nearest_neighbors()

    # Refinement on B
    try:
        sub_b.refine_atom_positions_using_center_of_mass(percent_to_nn=0.4)
        sub_b.refine_atom_positions_using_2d_gaussian(percent_to_nn=0.4)
    except Exception:
        # Fall back to center of mass only
        sub_b.refine_atom_positions_using_center_of_mass(percent_to_nn=0.4)

    return sub_a, sub_b, np.array(ideal_b_positions)


def compute_b_displacements(
    refined_b_positions: np.ndarray, ideal_b_positions: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute displacement vectors for B positions relative to nearest ideal centers.
    Returns dx, dy arrays aligned with refined_b_positions order.
    """
    tree = cKDTree(ideal_b_positions)
    _, idx = tree.query(refined_b_positions, k=1)
    matched_ideal = ideal_b_positions[idx]
    deltas = refined_b_positions - matched_ideal
    return deltas[:, 0], deltas[:, 1]
