import os
from pathlib import Path
from typing import Optional
import logging

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets

from config import DEFAULTS
from core import pipeline
from core import viz
from core import io_utils


class Worker(QtCore.QObject):
    finished = QtCore.Signal(object, object)  # result, error

    def __init__(self, image_path: str, gs: float, refine_sigma: float, sep: Optional[float], thr: Optional[float], output_dir: Optional[Path]):
        super().__init__()
        self.image_path = image_path
        self.gs = gs
        self.refine_sigma = refine_sigma
        self.sep = sep
        self.thr = thr
        self.output_dir = output_dir

    @QtCore.Slot()
    def run(self):
        try:
            result = pipeline.run_pipeline(
                self.image_path,
                gaussian_sigma=self.gs,
                background_sigma=None,
                roi=None,
                separation=self.sep,
                threshold=self.thr,
                refine_sigma=self.refine_sigma,
                nm_per_pixel=getattr(self, "nm_per_px", None),
                output_dir=str(self.output_dir) if self.output_dir else None,
            )
            self.finished.emit(result, None)
        except Exception as exc:  # pragma: no cover - GUI path
            self.finished.emit(None, exc)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Atomap STEM Analyzer (Qt)")
        self.resize(1200, 800)

        self.image_path: Optional[str] = None
        self.result = None
        self.thread: Optional[QtCore.QThread] = None
        self.output_dir: Optional[Path] = None
        self.logger = logging.getLogger("stem_atomap")

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        root_layout = QtWidgets.QHBoxLayout(central)

        # Left panel (controls)
        left = QtWidgets.QVBoxLayout()
        self.btn_open = QtWidgets.QPushButton("选择图像")
        self.btn_open.clicked.connect(self.choose_image)
        left.addWidget(self.btn_open)

        self.status = QtWidgets.QLabel("未选择文件")
        left.addWidget(self.status)

        form = QtWidgets.QFormLayout()
        self.in_sigma = QtWidgets.QLineEdit(str(DEFAULTS["gaussian_sigma"]))
        self.in_refine = QtWidgets.QLineEdit("1.0")
        self.in_sep = QtWidgets.QLineEdit("")
        self.in_thr = QtWidgets.QLineEdit("")
        self.in_scale = QtWidgets.QLineEdit("")  # nm per pixel
        form.addRow("Gaussian σ", self.in_sigma)
        form.addRow("Refine σ", self.in_refine)
        form.addRow("Separation(px，可空)", self.in_sep)
        form.addRow("Threshold_rel(可空)", self.in_thr)
        form.addRow("比例尺 nm/px", self.in_scale)
        left.addLayout(form)

        self.btn_run = QtWidgets.QPushButton("运行")
        self.btn_run.clicked.connect(self.run_pipeline)
        left.addWidget(self.btn_run)

        self.btn_export = QtWidgets.QPushButton("导出结果目录")
        self.btn_export.clicked.connect(self.export_results)
        left.addWidget(self.btn_export)
        left.addStretch()

        # Right panel (outputs)
        right = QtWidgets.QGridLayout()
        self.preview_label = QtWidgets.QLabel("原始/预处理图")
        self.preview_label.setAlignment(QtCore.Qt.AlignCenter)
        self.overlay_label = QtWidgets.QLabel("A/B峰叠加")
        self.overlay_label.setAlignment(QtCore.Qt.AlignCenter)
        self.arrows_label = QtWidgets.QLabel("位移箭头")
        self.arrows_label.setAlignment(QtCore.Qt.AlignCenter)
        self.heatmap_label = QtWidgets.QLabel("位移热图")
        self.heatmap_label.setAlignment(QtCore.Qt.AlignCenter)
        for lbl in (self.preview_label, self.overlay_label, self.arrows_label, self.heatmap_label):
            lbl.setMinimumSize(400, 300)
        right.addWidget(self.preview_label, 0, 0)
        right.addWidget(self.overlay_label, 0, 1)
        right.addWidget(self.arrows_label, 1, 0)
        right.addWidget(self.heatmap_label, 1, 1)

        root_layout.addLayout(left, 1)
        root_layout.addLayout(right, 3)

        # Status bar
        self.statusBar().showMessage("就绪")

    def choose_image(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "选择图像",
            "",
            "Images (*.dm3 *.dm4 *.tif *.tiff *.png *.jpg *.jpeg);;All Files (*)",
        )
        if path:
            self.image_path = path
            self.status.setText(f"已选择: {path}")
            self.statusBar().showMessage("已选择图像，准备运行")
            img = io_utils.load_image(path)
            self._show_array(img, self.preview_label)

    def run_pipeline(self):
        if not self.image_path:
            QtWidgets.QMessageBox.warning(self, "提示", "请先选择图像")
            return
        try:
            gs = float(self.in_sigma.text() or DEFAULTS["gaussian_sigma"])
            rs = float(self.in_refine.text() or 1.0)
            sep = self._maybe_float(self.in_sep.text())
            thr = self._maybe_float(self.in_thr.text())
            scale = self._maybe_float(self.in_scale.text())
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "提示", "参数格式错误")
            return

        self.status.setText("运行中...")
        self.statusBar().showMessage("运行中...")
        self.btn_run.setEnabled(False)

        # Worker thread
        self.thread = QtCore.QThread()
        self.worker = Worker(self.image_path, gs, rs, sep, thr, self.output_dir)
        self.worker.nm_per_px = scale
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._on_finished)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    @QtCore.Slot(object, object)
    def _on_finished(self, result, error):
        self.btn_run.setEnabled(True)
        if error:
            self.status.setText("失败")
            self.statusBar().showMessage("失败")
            self.logger.error(f"Pipeline failed: {error}")
            QtWidgets.QMessageBox.critical(self, "错误", str(error))
            return
        self.result = result
        self.output_dir = result.output_dir
        self.status.setText(f"完成 | 分辨率估计: {self.result.separation:.2f}px")
        self.statusBar().showMessage(f"完成，输出目录: {self.output_dir}")
        self._show_array(self.result.image, self.preview_label)
        # Load saved overlays
        self._load_pixmap(self.output_dir / "peaks_overlay.png", self.overlay_label)
        self._load_pixmap(self.output_dir / "displacement_arrows.png", self.arrows_label)
        self._load_pixmap(self.output_dir / "displacement_heatmap.png", self.heatmap_label)

    def _show_array(self, array: np.ndarray, label: QtWidgets.QLabel):
        arr = array - np.nanmin(array)
        max_val = np.nanmax(arr)
        if max_val > 0:
            arr = arr / max_val * 255.0
        img = QtGui.QImage(arr.astype(np.uint8), arr.shape[1], arr.shape[0], arr.shape[1], QtGui.QImage.Format_Grayscale8)
        pixmap = QtGui.QPixmap.fromImage(img).scaled(512, 512, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        label.setPixmap(pixmap)

    def _load_pixmap(self, path: Path, label: QtWidgets.QLabel):
        if path and path.exists():
            pixmap = QtGui.QPixmap(str(path)).scaled(512, 512, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            label.setPixmap(pixmap)

    def export_results(self):
        if not self.result:
            QtWidgets.QMessageBox.information(self, "提示", "请先运行分析")
            return
        if self.output_dir:
            QtWidgets.QMessageBox.information(self, "导出完成", f"结果已保存到 {self.output_dir}")
        else:
            QtWidgets.QMessageBox.information(self, "提示", "无输出目录信息")

    @staticmethod
    def _maybe_float(text: str) -> Optional[float]:
        text = text.strip()
        return float(text) if text else None
