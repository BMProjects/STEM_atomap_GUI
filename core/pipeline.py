from dataclasses import dataclass
import logging
import os
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import tqdm

# Avoid numba caching/jit issues in hyperspy/atomap on constrained filesystems
os.environ.setdefault("NUMBA_DISABLE_CACHING", "1")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
# Silence tqdm notebook warnings
os.environ.setdefault("TQDM_DISABLE", "1")
try:
    import tqdm.notebook as tnb
    tnb.tqdm = tqdm.tqdm
except Exception:
    pass

from . import lattice as lattice_mod
from . import metrics
from . import preprocess
from . import io_utils
from . import viz


LOG_DIR = Path(__file__).resolve().parent.parent / "log"
LOG_DIR.mkdir(exist_ok=True)
logger = logging.getLogger("stem_atomap")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(LOG_DIR / "app.log", encoding="utf-8")
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    fh.setFormatter(fmt)
    logger.addHandler(fh)


@dataclass
class PipelineResult:
    image: np.ndarray
    sublattice_a: object
    sublattice_b: object
    peaks_a: np.ndarray
    peaks_b: np.ndarray
    ideal_b: np.ndarray
    separation: float
    displacement: Dict[str, np.ndarray]
    strain: Dict[str, np.ndarray]
    output_dir: Path


def run_pipeline(
    image_path: str,
    gaussian_sigma: float = 1.0,
    background_sigma: Optional[float] = None,
    roi: Optional[Tuple[int, int, int, int]] = None,
    separation: Optional[float] = None,
    threshold: Optional[float] = None,
    refine_sigma: float = 1.0,
    reference: str = "average",
    nm_per_pixel: Optional[float] = None,
    output_dir: Optional[str] = None,
) -> PipelineResult:
    """
    Full pipeline: load -> preprocess -> lattice detection/refine -> displacement/strain.
    """
    logger.info(f"Starting pipeline | image={image_path}")
    raw = io_utils.load_image(image_path)
    img = preprocess.preprocess_image(raw, gaussian_sigma=gaussian_sigma, background_sigma=background_sigma, roi=roi)
    logger.info("Preprocess done")

    # A/B sublattice construction
    sep = separation
    if sep is None:
        sep = lattice_mod._estimate_separation_from_fft(img)
    if sep is None or sep <= 0:
        raise ValueError("Failed to estimate lattice separation; please provide separation in pixels.")
    logger.info(f"Using separation: {sep}")

    sub_a, sub_b, ideal_b = lattice_mod.build_sublattices(
        img,
        separation=sep,
        threshold=threshold,
        refine_sigma=refine_sigma,
    )
    logger.info(f"Sublattices built: A={len(sub_a.atom_positions)}, B={len(sub_b.atom_positions)}")
    peaks_a = sub_a.atom_positions
    peaks_b = sub_b.atom_positions

    dx_px, dy_px = lattice_mod.compute_b_displacements(peaks_b, ideal_b)
    mag_px = np.hypot(dx_px, dy_px)
    if nm_per_pixel:
        dx_nm = dx_px * nm_per_pixel
        dy_nm = dy_px * nm_per_pixel
        mag_nm = mag_px * nm_per_pixel
    else:
        dx_nm = dy_nm = mag_nm = None

    disp = {
        "dx": dx_px,
        "dy": dy_px,
        "mag": mag_px,
        "dx_nm": dx_nm,
        "dy_nm": dy_nm,
        "mag_nm": mag_nm,
    }
    strain = {}  # Placeholder; strain calculation requires get_strain_map which may be absent in 0.4.2

    # Save standard outputs
    out_dir = Path(output_dir) if output_dir else Path("outputs") / Path(image_path).stem
    out_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Saving outputs to {out_dir}")
    try:
        io_utils.save_png(img, out_dir / "preprocessed.png")
        io_utils.save_csv(peaks_a, header="x,y", path=out_dir / "peaks_a.csv")
        io_utils.save_csv(peaks_b, header="x,y", path=out_dir / "peaks_b.csv")
        viz.save_peaks_overlay(img, peaks_a, peaks_b, out_dir / "peaks_overlay.png")
        io_utils.save_csv(np.column_stack((dx_px, dy_px)), header="dx,dy (pixels)", path=out_dir / "displacement.csv")
        viz.save_displacement_arrows(
            img,
            ideal_b,
            dx_px,
            dy_px,
            out_dir / "displacement_arrows.png",
            arrow_scale=sep if sep else 1.0,
            color="yellow",
            scale_nm_per_px=nm_per_pixel,
        )
        viz.save_displacement_heatmap(img, peaks_b, mag_px, out_dir / "displacement_heatmap.png")
        if dx_nm is not None:
            io_utils.save_csv(np.column_stack((dx_nm, dy_nm)), header="dx,dy (nm)", path=out_dir / "displacement_nm.csv")
    except Exception as exc:
        logger.exception(f"Failed saving outputs: {exc}")
        raise

    return PipelineResult(
        image=img,
        sublattice_a=sub_a,
        sublattice_b=sub_b,
        peaks_a=peaks_a,
        peaks_b=peaks_b,
        ideal_b=ideal_b,
        separation=sep,
        displacement=disp,
        strain=strain,
        output_dir=out_dir,
    )
