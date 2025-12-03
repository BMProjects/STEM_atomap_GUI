import sys
import os
import tqdm
from PySide6 import QtWidgets

# Silence tqdm notebook warnings
os.environ.setdefault("TQDM_DISABLE", "1")
try:
    import tqdm.notebook as tnb
    tnb.tqdm = tqdm.tqdm
except Exception:
    pass

from ui_qt.main_window import MainWindow


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
