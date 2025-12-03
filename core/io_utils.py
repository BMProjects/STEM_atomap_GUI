import os
from pathlib import Path
from typing import Tuple, Union

import hyperspy.api as hs
import numpy as np
from PIL import Image


def load_image(path: Union[str, Path]) -> np.ndarray:
    """
    Load STEM/HAADF image. Supports dm3/dm4 via hyperspy, and common image formats via PIL.
    Returns a 2D float64 numpy array.
    """
    path = Path(path)
    ext = path.suffix.lower()
    if ext in {".dm3", ".dm4", ".hspy", ".emd"}:
        sig = hs.load(path, lazy=False)
        data = np.asarray(sig.data, dtype=np.float64)
    else:
        with Image.open(path) as img:
            data = np.asarray(img.convert("L"), dtype=np.float64)
    return data


def crop_roi(image: np.ndarray, roi: Tuple[int, int, int, int]) -> np.ndarray:
    x1, y1, x2, y2 = roi
    return image[y1:y2, x1:x2]


def save_csv(array: np.ndarray, header: str, path: Union[str, Path]) -> None:
    os.makedirs(Path(path).parent, exist_ok=True)
    np.savetxt(path, array, delimiter=",", header=header, comments="")


def save_png(image: np.ndarray, path: Union[str, Path]) -> None:
    os.makedirs(Path(path).parent, exist_ok=True)
    # Normalize to 0-255 for viewing
    arr = image - np.nanmin(image)
    if np.nanmax(arr) > 0:
        arr = arr / np.nanmax(arr) * 255.0
    Image.fromarray(arr.astype(np.uint8)).save(path)
