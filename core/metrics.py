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


def compute_strain_from_displacement(
    points: np.ndarray,
    dx: np.ndarray,
    dy: np.ndarray,
    image_shape: tuple,
    grid_size: int = 200,
) -> Dict[str, np.ndarray]:
    """
    Compute strain tensor from scattered displacement data.

    Uses interpolation to create a regular grid, then computes gradients.

    Strain tensor components:
        ε_xx = ∂u/∂x
        ε_yy = ∂v/∂y
        ε_xy = 0.5 * (∂u/∂y + ∂v/∂x)  (engineering shear strain)
        ω = 0.5 * (∂v/∂x - ∂u/∂y)  (rotation)

    Args:
        points: (N, 2) array of atom positions (x, y).
        dx: (N,) array of x-displacements (u).
        dy: (N,) array of y-displacements (v).
        image_shape: (height, width) of the image.
        grid_size: Resolution of interpolation grid.

    Returns:
        Dictionary with exx, eyy, exy, rotation arrays and grid coordinates.
    """
    from scipy.interpolate import griddata

    h, w = image_shape

    # Create regular grid with slight margin
    margin_factor = 0.01
    grid_x, grid_y = np.mgrid[
        -margin_factor*w : w*(1+margin_factor) : complex(0, grid_size),
        -margin_factor*h : h*(1+margin_factor) : complex(0, grid_size)
    ]

    # Interpolate displacement fields to regular grid using linear method
    u_grid = griddata(points, dx, (grid_x, grid_y), method="linear", fill_value=np.nan)
    v_grid = griddata(points, dy, (grid_x, grid_y), method="linear", fill_value=np.nan)
    
    # Fill remaining NaN values with nearest neighbor
    if np.any(np.isnan(u_grid)):
        u_grid_nearest = griddata(points, dx, (grid_x, grid_y), method="nearest")
        u_grid[np.isnan(u_grid)] = u_grid_nearest[np.isnan(u_grid)]
    if np.any(np.isnan(v_grid)):
        v_grid_nearest = griddata(points, dy, (grid_x, grid_y), method="nearest")
        v_grid[np.isnan(v_grid)] = v_grid_nearest[np.isnan(v_grid)]

    # Compute pixel spacing on the interpolation grid
    dx_spacing = w / (grid_size - 1)
    dy_spacing = h / (grid_size - 1)

    # Compute gradients
    # np.gradient returns (d/dy, d/dx) for 2D arrays with axis order (y, x)
    # But our grid is (x, y), so we swap
    du_dx, du_dy = np.gradient(u_grid, dx_spacing, dy_spacing)
    dv_dx, dv_dy = np.gradient(v_grid, dx_spacing, dy_spacing)

    # Strain tensor components
    exx = du_dx  # ε_xx = ∂u/∂x
    eyy = dv_dy  # ε_yy = ∂v/∂y
    exy = 0.5 * (du_dy + dv_dx)  # ε_xy (shear)
    rotation = 0.5 * (dv_dx - du_dy)  # ω (rotation in radians)

    return {
        "exx": exx,
        "eyy": eyy,
        "exy": exy,
        "rotation": rotation,
        "rotation_deg": np.degrees(rotation),
        "grid_x": grid_x,
        "grid_y": grid_y,
        "u_grid": u_grid,
        "v_grid": v_grid,
        "source_points": points,  # Original atom positions for masking
    }

