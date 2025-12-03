from typing import Dict, Optional

from atomap.atom_lattice import Atom_Lattice
import numpy as np


def compute_displacement(lattice: Atom_Lattice, reference: str = "average", image_shape: Optional[tuple] = None) -> Dict[str, np.ndarray]:
    if hasattr(lattice, "get_displacement_map"):
        disp_map = lattice.get_displacement_map(reference=reference)
        return {
            "object": disp_map,
            "dx": disp_map.displacement_x,
            "dy": disp_map.displacement_y,
            "magnitude": disp_map.displacement_magnitude,
        }
    # Fallback: zero arrays
    shape = image_shape or getattr(lattice, "image", None)
    if shape is not None and hasattr(shape, "shape"):
        shape = shape.shape
    if shape is None:
        shape = (1, 1)
    dx = np.zeros(shape, dtype=float)
    dy = np.zeros(shape, dtype=float)
    return {"object": None, "dx": dx, "dy": dy, "magnitude": np.hypot(dx, dy)}


def compute_strain(lattice: Atom_Lattice, reference: Optional[str] = "average", image_shape: Optional[tuple] = None) -> Dict[str, np.ndarray]:
    if hasattr(lattice, "get_strain_map"):
        strain_map = lattice.get_strain_map(reference=reference)
        return {
            "object": strain_map,
            "exx": strain_map.exx,
            "eyy": strain_map.eyy,
            "exy": strain_map.exy,
        }
    shape = image_shape or getattr(lattice, "image", None)
    if shape is not None and hasattr(shape, "shape"):
        shape = shape.shape
    if shape is None:
        shape = (1, 1)
    return {
        "object": None,
        "exx": np.zeros(shape, dtype=float),
        "eyy": np.zeros(shape, dtype=float),
        "exy": np.zeros(shape, dtype=float),
    }
