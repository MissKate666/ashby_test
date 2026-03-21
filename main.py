import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATASET = BASE_DIR / "materials_for_project" / "Ashby_Chart_Regions.csv"


class AshbyDiagramWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.df = None
        self.current_dataset_path = None
        self.init_ui()
        self.load_default_dataset()

    def init_ui(self):
        self.setWindowTitle('Ashby Diagram Generator')
        self.setGeometry(100, 100, 1300, 900)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)

        control_panel = QWidget()
        control_panel.setMaximumWidth(360)
        control_layout = QVBoxLayout(control_panel)

        file_group = QGroupBox("Dataset")
        file_layout = QVBoxLayout()

        self.load_btn = QPushButton('Load Ashby CSV')
        self.load_btn.clicked.connect(self.load_csv)
        file_layout.addWidget(self.load_btn)

        self.reset_btn = QPushButton('Load default dataset')
        self.reset_btn.clicked.connect(self.load_default_dataset)
        file_layout.addWidget(self.reset_btn)

        self.file_label = QLabel('No dataset loaded')
        self.file_label.setWordWrap(True)
        file_layout.addWidget(self.file_label)

        file_group.setLayout(file_layout)
        control_layout.addWidget(file_group)

        info_group = QGroupBox("Chart info")
        info_layout = QVBoxLayout()

        self.data_info_label = QLabel('No data loaded')
        self.data_info_label.setWordWrap(True)
        info_layout.addWidget(self.data_info_label)

        info_group.setLayout(info_layout)
        control_layout.addWidget(info_group)

        self.update_btn = QPushButton('Redraw chart')
        self.update_btn.clicked.connect(self.update_plot)
        self.update_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 8px; }"
        )
        control_layout.addWidget(self.update_btn)
        control_layout.addStretch()

        plot_panel = QWidget()
        plot_layout = QVBoxLayout(plot_panel)

        self.figure = plt.figure(figsize=(12, 9))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        plot_layout.addWidget(self.toolbar)
        plot_layout.addWidget(self.canvas)

        main_layout.addWidget(control_panel)
        main_layout.addWidget(plot_panel, stretch=1)

    def load_default_dataset(self):
        self.load_dataset(DEFAULT_DATASET)

    def load_csv(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open Ashby CSV Dataset",
            str(DEFAULT_DATASET.parent),
            "CSV Files (*.csv);;All Files (*)",
        )
        if file_name:
            self.load_dataset(Path(file_name))

    def load_dataset(self, file_path: Path):
        try:
            df = pd.read_csv(file_path)
            df.columns = df.columns.str.strip()
            self.validate_dataset(df)
            self.df = df
            self.current_dataset_path = file_path
            self.file_label.setText(f'Loaded: {file_path.name}')
            self.update_data_info()
            self.update_plot()
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Failed to load dataset:\n{exc}")

    @staticmethod
    def validate_dataset(df: pd.DataFrame):
        required_columns = {
            'label',
            'x_center',
            'y_center',
            'bubble_size',
            'color',
            'description',
        }
        missing = required_columns.difference(df.columns)
        if missing:
            missing_text = ', '.join(sorted(missing))
            raise ValueError(f'Missing required columns: {missing_text}')

    def update_data_info(self):
        if self.df is None:
            self.data_info_label.setText('No data loaded')
            return

        dataset_name = self.current_dataset_path.name if self.current_dataset_path else 'unknown'
        info_text = [
            f"Dataset: {dataset_name}",
            f"Primary materials: {len(self.df)}",
            "Axes: Toughness (kJ/m²) vs Strength (MPa)",
            "Chart source: CSV-driven circles",
            "Autodraw: enabled after dataset load",
        ]
        self.data_info_label.setText('\n'.join(info_text))

    def add_region(self, ax, row):
        ax.scatter(
            row['x_center'],
            row['y_center'],
            s=row['bubble_size'],
            c=row['color'],
            alpha=0.58,
            edgecolors='black',
            linewidth=1.2,
            marker='o',
            zorder=2,
        )
        ax.text(
            row['x_center'],
            row['y_center'],
            row['label'],
            ha='center',
            va='center',
            fontsize=10,
            weight='bold',
            zorder=3,
        )

    def update_plot(self):
        if self.df is None:
            QMessageBox.warning(self, 'Warning', 'Please load a CSV file first.')
            return

        try:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.set_xscale('log')
            ax.set_yscale('log')
            ax.set_xlim(0.001, 100)
            ax.set_ylim(0.1, 10000)

            for _, row in self.df.iterrows():
                self.add_region(ax, row)

            ax.set_xlabel('TOUGHNESS (kJ/m²)', fontsize=12)
            ax.set_ylabel('STRENGTH (MPa)', fontsize=12)
            ax.set_title('Ashby Chart\nStrength vs Toughness', fontsize=18, fontweight='bold')
            ax.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.6, zorder=0)

            description_lines = [
                f"• {row['label']}: {row['description']}" for _, row in self.df.iterrows()
            ]
            ax.text(
                1.03,
                0.98,
                '\n'.join(description_lines),
                transform=ax.transAxes,
                va='top',
                fontsize=9,
                bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.85),
            )

            for spine in ax.spines.values():
                spine.set_linewidth(1.5)

            self.figure.tight_layout()
            self.canvas.draw()
            self.update_data_info()
        except Exception as exc:
            QMessageBox.critical(self, 'Error', f'Failed to update plot:\n{exc}')


def main():
    app = QApplication(sys.argv)
    window = AshbyDiagramWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
