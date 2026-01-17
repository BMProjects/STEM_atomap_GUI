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




class ScalableImageLabel(QtWidgets.QLabel):
    """QLabel that scales its pixmap to fit the widget while maintaining aspect ratio."""

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self._pixmap = None
        # Ignore size policy so the widget doesn't force resize based on content
        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)

    def setPixmap(self, pixmap):
        """Store pixmap and trigger repaint without layout recursion."""
        self._pixmap = pixmap
        # Clear text if any (standard QLabel behavior)
        if pixmap and not pixmap.isNull():
            self.setText("")
        self.update()

    def paintEvent(self, event):
        """Custom paint event to draw scaled pixmap."""
        if self._pixmap and not self._pixmap.isNull():
            painter = QtGui.QPainter(self)
            painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
            
            # Calculate target rect to center image while keeping aspect ratio
            rect = self.rect()
            scaled_size = self._pixmap.size().scaled(rect.size(), QtCore.Qt.KeepAspectRatio)
            
            # Center coordinates
            x = (rect.width() - scaled_size.width()) // 2
            y = (rect.height() - scaled_size.height()) // 2
            
            target_rect = QtCore.QRect(x, y, scaled_size.width(), scaled_size.height())
            painter.drawPixmap(target_rect, self._pixmap)
        else:
            # Fallback to standard paint (e.g. for text)
            super().paintEvent(event)



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

        # Left panel (controls) - Compact sidebar
        left_widget = QtWidgets.QWidget()
        left_widget.setMaximumWidth(180)  # Further reduced sidebar width
        left = QtWidgets.QVBoxLayout(left_widget)
        left.setContentsMargins(5, 5, 5, 5)
        left.setSpacing(6)

        self.btn_open = QtWidgets.QPushButton("选择图像")
        self.btn_open.clicked.connect(self.choose_image)
        left.addWidget(self.btn_open)

        self.status = QtWidgets.QLabel("未选择文件")
        self.status.setWordWrap(True)
        # Removed MaximumHeight constraint to allow auto-expand
        left.addWidget(self.status)

        # Parameter inputs - compact layout
        params_group = QtWidgets.QGroupBox("参数")
        form = QtWidgets.QVBoxLayout(params_group)
        form.setSpacing(2)
        form.setContentsMargins(4, 8, 4, 4)
        
        self.in_sigma = QtWidgets.QLineEdit(str(DEFAULTS["gaussian_sigma"]))
        self.in_refine = QtWidgets.QLineEdit("1.0")
        self.in_sep = QtWidgets.QLineEdit("")
        self.in_sep.setToolTip("Auto-estimated from FFT if empty (average lattice spacing)")
        self.in_thr = QtWidgets.QLineEdit("")
        self.in_scale = QtWidgets.QLineEdit("")  # nm per pixel
        
        for label, widget in [
            ("Gaussian σ:", self.in_sigma),
            ("Refine σ:", self.in_refine),
            ("Separation (px):", self.in_sep),
            ("Threshold:", self.in_thr),
            ("比例尺 (nm/px):", self.in_scale),
        ]:
            lbl = QtWidgets.QLabel(label)
            lbl.setMaximumHeight(18)
            form.addWidget(lbl)
            widget.setMaximumHeight(24)
            form.addWidget(widget)
        
        left.addWidget(params_group)

        self.btn_run = QtWidgets.QPushButton("运行")
        self.btn_run.clicked.connect(self.run_pipeline)
        left.addWidget(self.btn_run)

        self.btn_export = QtWidgets.QPushButton("导出结果目录")
        self.btn_export.clicked.connect(self.export_results)
        left.addWidget(self.btn_export)
        left.addStretch()

        # Right panel (outputs) - Tabbed interface
        self.tab_widget = QtWidgets.QTabWidget()

        def create_image_label(text: str) -> ScalableImageLabel:
            lbl = ScalableImageLabel(text)
            lbl.setMinimumSize(50, 50)  # Minimal size to avoid collapse
            return lbl

        # Tab 1: Overview (2x2 grid)
        overview_widget = QtWidgets.QWidget()
        overview_layout = QtWidgets.QGridLayout(overview_widget)
        # Uniform stretch factors for 2x2 grid
        overview_layout.setRowStretch(0, 1)
        overview_layout.setRowStretch(1, 1)
        overview_layout.setColumnStretch(0, 1)
        overview_layout.setColumnStretch(1, 1)
        
        self.preview_label = create_image_label("原始/预处理图")
        self.overlay_label = create_image_label("A/B峰叠加")
        self.arrows_label = create_image_label("位移箭头")
        self.heatmap_label = create_image_label("位移热图")
        overview_layout.addWidget(self.preview_label, 0, 0)
        overview_layout.addWidget(self.overlay_label, 0, 1)
        overview_layout.addWidget(self.arrows_label, 1, 0)
        overview_layout.addWidget(self.heatmap_label, 1, 1)
        self.tab_widget.addTab(overview_widget, "概览")

        # Tab 2: Color-coded vectors
        vectors_widget = QtWidgets.QWidget()
        vectors_layout = QtWidgets.QHBoxLayout(vectors_widget)
        self.angle_arrows_label = create_image_label("角度着色矢量图")
        self.mag_arrows_label = create_image_label("模长着色矢量图")
        vectors_layout.addWidget(self.angle_arrows_label, 1)
        vectors_layout.addWidget(self.mag_arrows_label, 1)
        self.tab_widget.addTab(vectors_widget, "彩色矢量图")

        # Tab 3: Statistics
        stats_widget = QtWidgets.QWidget()
        stats_layout = QtWidgets.QHBoxLayout(stats_widget)
        self.histogram_label = create_image_label("位移模长直方图")
        self.polar_label = create_image_label("位移角度极图")
        stats_layout.addWidget(self.histogram_label, 1)
        stats_layout.addWidget(self.polar_label, 1)
        self.tab_widget.addTab(stats_widget, "统计分布")

        # Tab 4: Strain
        strain_widget = QtWidgets.QWidget()
        strain_layout = QtWidgets.QVBoxLayout(strain_widget)
        self.strain_combined_label = create_image_label("应变张量分析")
        strain_layout.addWidget(self.strain_combined_label)
        self.tab_widget.addTab(strain_widget, "应变分析")

        root_layout.addWidget(left_widget)
        root_layout.addWidget(self.tab_widget, 1)

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

        # Tab 1: Overview - Load saved overlays
        self._load_pixmap(self.output_dir / "peaks_overlay.png", self.overlay_label)
        self._load_pixmap(self.output_dir / "displacement_arrows.png", self.arrows_label)
        self._load_pixmap(self.output_dir / "displacement_heatmap.png", self.heatmap_label)

        # Tab 2: Color-coded vectors
        self._load_pixmap(self.output_dir / "displacement_arrows_angle.png", self.angle_arrows_label)
        self._load_pixmap(self.output_dir / "displacement_arrows_magnitude.png", self.mag_arrows_label)

        # Tab 3: Statistics
        self._load_pixmap(self.output_dir / "displacement_histogram.png", self.histogram_label)
        self._load_pixmap(self.output_dir / "displacement_polar.png", self.polar_label)

        # Tab 4: Strain
        self._load_pixmap(self.output_dir / "strain_combined.png", self.strain_combined_label)

    def _show_array(self, array: np.ndarray, label: ScalableImageLabel):
        """Display numpy array in QLabel with auto-scaling."""
        arr = array - np.nanmin(array)
        max_val = np.nanmax(arr)
        if max_val > 0:
            arr = arr / max_val * 255.0
        img = QtGui.QImage(arr.astype(np.uint8), arr.shape[1], arr.shape[0], arr.shape[1], QtGui.QImage.Format_Grayscale8)
        pixmap = QtGui.QPixmap.fromImage(img)
        label.setPixmap(pixmap)

    def _load_pixmap(self, path: Path, label: ScalableImageLabel):
        """Load image from file into QLabel with auto-scaling."""
        if path and path.exists():
            pixmap = QtGui.QPixmap(str(path))
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
