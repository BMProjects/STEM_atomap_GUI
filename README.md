# STEM Atomap GUI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

A powerful, user-friendly desktop application for **Scanning Transmission Electron Microscopy (STEM)** atomic position analysis. Built on the robust [Atomap](https://atomap.org/) library and PySide6.

This tool automates the quantification of lattice distortions, polarization, and strain fields in atomic-resolution images, producing publication-quality visualizations and statistical data.

---

## 🚀 Key Features

* **Automated Lattice Analysis**: Detects A/B sublattices and computes atomic displacements.
* **Rich Visualization**:
  * **Color-coded Vector Maps**: Visualize displacement direction (HSV angle) and magnitude.
  * **Strain Mapping**: Full strain tensor ($\varepsilon_{xx}, \varepsilon_{yy}, \varepsilon_{xy}$) and rotation analysis.
  * **Heatmaps**: Interpolated magnitude maps with smart edge masking.
* **Interactive GUI**: Real-time parameter tuning, scale bar support, and tabbed result views.
* **Statistical Tools**: Histograms and polar plots for displacement analysis.
* **Publication Ready**: Automatic scale bars, physical unit conversion (nm/pm), and high-res outputs.

## 📚 Documentation

👉 **[Read the User Manual](docs/USER_MANUAL.md)** for detailed usage instructions, algorithm explanations, and parameter guides.

## 🛠️ Installation

1. **Clone the repository**:

    ```bash
    git clone https://github.com/your-username/STEM-Atomap-GUI.git
    cd STEM-Atomap-GUI
    ```

2. **Create a virtual environment** (recommended):

    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # Linux/Mac
    source .venv/bin/activate
    ```

3. **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

## ⚡ Quick Start

1. **Run the GUI**:

    ```bash
    python main.py
    ```

2. **Analyze**:
    * Click **"Select Image"** to load a `.dm3` or `.tif` file.
    * (Optional) Adjust `Gaussian σ` or `Separation` in the sidebar.
    * Click **"Run"**.
    * Explore results in the "Overview", "Color Vectors", and "Strain Analysis" tabs.

## 🏗️ Structure

* `main.py`: Entry point for the GUI.
* `core/`: Core algorithms (preprocessing, metrics, visualization).
* `ui_qt/`: Interface code.
* `docs/`: Documentation.

## 🤝 Contributing

Contributions are welcome! Please verify changes with the test suite:

```bash
python tests/test_pipeline.py
```

## 📄 License

This project is licensed under the MIT License.
