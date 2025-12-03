from typing import Optional, Tuple

import numpy as np
from scipy.ndimage import gaussian_filter


def normalize(image: np.ndarray) -> np.ndarray:
    """Normalize to 0-1."""
    img = image.astype(np.float64)
    img -= img.min()
    max_val = img.max()
    if max_val > 0:
        img /= max_val
    return img


def remove_background(image: np.ndarray, sigma: float = 10.0) -> np.ndarray:
    """Simple background removal by subtracting a blurred version."""
    blurred = gaussian_filter(image, sigma=sigma)
    corrected = image - blurred
    corrected -= corrected.min()
    return corrected


def preprocess_image(
    image: np.ndarray,
    gaussian_sigma: float = 1.0,
    background_sigma: Optional[float] = None,
    roi: Optional[Tuple[int, int, int, int]] = None,
) -> np.ndarray:
    """
    Basic preprocessing: optional ROI crop, background removal, and Gaussian smoothing.
    """
    img = image
    if roi is not None:
        x1, y1, x2, y2 = roi
        img = img[y1:y2, x1:x2]
    if background_sigma:
        img = remove_background(img, sigma=background_sigma)
    if gaussian_sigma and gaussian_sigma > 0:
        img = gaussian_filter(img, sigma=gaussian_sigma)
    return normalize(img)
