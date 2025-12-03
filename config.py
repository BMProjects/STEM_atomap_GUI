DEFAULTS = {
    "gaussian_sigma": 1.0,
    "background_poly_order": 0,
    "min_separation": None,  # 如果为空，使用 FFT 推断
    "peak_threshold": None,  # 可让 atomap 自动估计
    "refine_sigma": 1.0,
    "roi": None,  # (x1, y1, x2, y2) 或 None
}
