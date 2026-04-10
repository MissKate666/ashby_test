import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.patches import Polygon as MplPolygon
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from shapely.geometry import MultiPoint, Point, Polygon


class AshbyDiagramWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.df = None
        self.group_map = None
        self.dragging_line = False
        self.condition_intercept = None
        self.line_artist = None
        self.last_suitable_df = pd.DataFrame()
        self.default_paths = {
            "groups": Path("materials_for_project/Group_materials.csv"),
            "subgroups": Path("materials_for_project/Subgroup_materials.csv"),
            "materials": Path("materials_for_project/Dataset_for_Ashby.csv"),
        }
        self.init_ui()
        self.load_default_data()

    def init_ui(self):
        self.setWindowTitle("Ashby Selector")
        self.setGeometry(100, 80, 1450, 900)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        panel = QWidget()
        panel.setMaximumWidth(360)
        panel_layout = QVBoxLayout(panel)

        cond_group = QGroupBox("Условия")
        cond_layout = QFormLayout()
        self.condition_combo = QComboBox()
        self.condition_combo.addItems(["Лёгкость (E/ρ)", "Прочность (σ/ρ)", "Изгиб (√E/ρ)"])
        self.condition_combo.currentIndexChanged.connect(self.on_condition_changed)
        cond_layout.addRow("Критерий:", self.condition_combo)

        self.preference_combo = QComboBox()
        self.preference_combo.addItems(["Высокое значение", "Низкое значение"])
        self.preference_combo.currentIndexChanged.connect(self.update_plot)
        cond_layout.addRow("Подходит:", self.preference_combo)
        cond_group.setLayout(cond_layout)
        panel_layout.addWidget(cond_group)

        axis_group = QGroupBox("Оси и диапазон (опционально)")
        axis_layout = QGridLayout()
        self.x_axis_combo = QComboBox()
        self.y_axis_combo = QComboBox()
        self.x_axis_combo.currentIndexChanged.connect(self.update_plot)
        self.y_axis_combo.currentIndexChanged.connect(self.update_plot)
        axis_layout.addWidget(QLabel("Ось X:"), 0, 0)
        axis_layout.addWidget(self.x_axis_combo, 0, 1)
        axis_layout.addWidget(QLabel("Ось Y:"), 1, 0)
        axis_layout.addWidget(self.y_axis_combo, 1, 1)

        self.x_min_input = QLineEdit()
        self.x_max_input = QLineEdit()
        self.y_min_input = QLineEdit()
        self.y_max_input = QLineEdit()
        for w in [self.x_min_input, self.x_max_input, self.y_min_input, self.y_max_input]:
            w.setPlaceholderText("пусто = без ограничения")
            w.editingFinished.connect(self.update_plot)

        axis_layout.addWidget(QLabel("X min"), 2, 0)
        axis_layout.addWidget(self.x_min_input, 2, 1)
        axis_layout.addWidget(QLabel("X max"), 3, 0)
        axis_layout.addWidget(self.x_max_input, 3, 1)
        axis_layout.addWidget(QLabel("Y min"), 4, 0)
        axis_layout.addWidget(self.y_min_input, 4, 1)
        axis_layout.addWidget(QLabel("Y max"), 5, 0)
        axis_layout.addWidget(self.y_max_input, 5, 1)
        axis_group.setLayout(axis_layout)
        panel_layout.addWidget(axis_group)

        self.preview_btn = QPushButton("Предварительный просмотр")
        self.preview_btn.clicked.connect(self.open_preview)
        panel_layout.addWidget(self.preview_btn)

        self.info_label = QLabel("Данные не загружены")
        self.info_label.setWordWrap(True)
        panel_layout.addWidget(self.info_label)
        panel_layout.addStretch(1)

        plot_panel = QWidget()
        plot_layout = QVBoxLayout(plot_panel)
        self.figure = plt.figure(figsize=(12, 8))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        plot_layout.addWidget(self.toolbar)
        plot_layout.addWidget(self.canvas)

        main_layout.addWidget(panel)
        main_layout.addWidget(plot_panel, stretch=1)

        self.canvas.mpl_connect("button_press_event", self.on_press)
        self.canvas.mpl_connect("button_release_event", self.on_release)
        self.canvas.mpl_connect("motion_notify_event", self.on_motion)
        self.canvas.mpl_connect("scroll_event", self.on_scroll)

    def load_default_data(self):
        try:
            groups = pd.read_csv(self.default_paths["groups"], encoding="utf-8-sig")
            subgroups = pd.read_csv(self.default_paths["subgroups"], encoding="utf-8-sig")
            materials = pd.read_csv(self.default_paths["materials"], encoding="utf-8-sig")

            groups.columns = groups.columns.str.strip()
            subgroups.columns = subgroups.columns.str.strip()
            materials.columns = materials.columns.str.strip()

            self.df = materials.merge(subgroups, on="subgroup_id", how="left").merge(groups, on="group_id", how="left")

            axis_cols = ["Density_kg_m3", "Youngs_Modulus_GPa", "Strength_MPa"]
            self.x_axis_combo.clear()
            self.y_axis_combo.clear()
            self.x_axis_combo.addItems(axis_cols)
            self.y_axis_combo.addItems(axis_cols)
            self.x_axis_combo.setCurrentText("Density_kg_m3")
            self.on_condition_changed()
            self.info_label.setText(f"Загружено материалов: {len(self.df)}")
            self.update_plot()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные:\n{e}")

    def current_condition_config(self):
        idx = self.condition_combo.currentIndex()
        if idx == 0:
            return {"y_col": "Youngs_Modulus_GPa", "m": 1.0, "label": "E/ρ", "to_b": lambda v: np.log10(v), "from_b": lambda b: 10 ** b}
        if idx == 1:
            return {"y_col": "Strength_MPa", "m": 1.0, "label": "σ/ρ", "to_b": lambda v: np.log10(v), "from_b": lambda b: 10 ** b}
        return {"y_col": "Youngs_Modulus_GPa", "m": 2.0, "label": "√E/ρ", "to_b": lambda v: 2 * np.log10(v), "from_b": lambda b: 10 ** (b / 2)}

    def on_condition_changed(self):
        cfg = self.current_condition_config()
        self.y_axis_combo.setCurrentText(cfg["y_col"])
        if self.df is not None and len(self.df):
            rho = pd.to_numeric(self.df["Density_kg_m3"], errors="coerce")
            if self.condition_combo.currentIndex() == 0:
                idx = pd.to_numeric(self.df["E_over_rho"], errors="coerce")
            elif self.condition_combo.currentIndex() == 1:
                idx = pd.to_numeric(self.df["Strength_over_rho"], errors="coerce")
            else:
                idx = pd.to_numeric(self.df["SqrtE_over_rho"], errors="coerce")
            idx = idx[(idx > 0) & np.isfinite(idx)]
            if len(idx):
                self.condition_intercept = cfg["to_b"](float(idx.median()))
        self.update_plot()

    @staticmethod
    def parse_optional_float(widget: QLineEdit):
        text = widget.text().strip().replace(",", ".")
        if not text:
            return None
        try:
            return float(text)
        except ValueError:
            return None

    def build_mask(self, df, x_col, y_col):
        x = pd.to_numeric(df[x_col], errors="coerce")
        y = pd.to_numeric(df[y_col], errors="coerce")
        mask = (x > 0) & (y > 0) & np.isfinite(x) & np.isfinite(y)

        cfg = self.current_condition_config()
        lx = np.log10(x[mask])
        ly = np.log10(y[mask])

        if self.condition_intercept is None:
            ratios = ly - cfg["m"] * lx
            self.condition_intercept = float(np.nanmedian(ratios))

        line_vals = cfg["m"] * lx + self.condition_intercept
        high_side = self.preference_combo.currentIndex() == 0
        if high_side:
            cond_mask = ly >= line_vals
        else:
            cond_mask = ly <= line_vals

        final_mask = pd.Series(False, index=df.index)
        final_mask.loc[mask.index[mask]] = cond_mask.values

        xmin = self.parse_optional_float(self.x_min_input)
        xmax = self.parse_optional_float(self.x_max_input)
        ymin = self.parse_optional_float(self.y_min_input)
        ymax = self.parse_optional_float(self.y_max_input)

        if xmin is not None:
            final_mask &= x >= xmin
        if xmax is not None:
            final_mask &= x <= xmax
        if ymin is not None:
            final_mask &= y >= ymin
        if ymax is not None:
            final_mask &= y <= ymax

        return x, y, final_mask, mask

    def rounded_patch_from_log_points(self, points_log, color, alpha, lw=1.2, zorder=2):
        if len(points_log) < 3:
            return None
        hull = MultiPoint(points_log).convex_hull
        if not isinstance(hull, Polygon):
            return None
        minx, miny, maxx, maxy = hull.bounds
        radius = max((maxx - minx), (maxy - miny)) * 0.08
        rounded = hull.buffer(radius).buffer(-radius)
        if rounded.is_empty:
            rounded = hull
        coords = np.array(rounded.exterior.coords)
        coords_lin = np.column_stack((10 ** coords[:, 0], 10 ** coords[:, 1]))
        return MplPolygon(coords_lin, closed=True, facecolor=color, edgecolor=color, alpha=alpha, linewidth=lw, zorder=zorder)

    def material_patch(self, x, y, color="#1f77b4"):
        logx, logy = np.log10(x), np.log10(y)
        r = 0.018
        angles = np.linspace(0, 2 * np.pi, 7)[:-1]
        points = [(logx + r * np.cos(a), logy + r * np.sin(a)) for a in angles]
        poly = Polygon(points)
        rounded = poly.buffer(r * 0.35).buffer(-r * 0.35)
        coords = np.array(rounded.exterior.coords)
        coords_lin = np.column_stack((10 ** coords[:, 0], 10 ** coords[:, 1]))
        return MplPolygon(coords_lin, closed=True, facecolor=color, edgecolor="white", alpha=0.85, linewidth=0.5, zorder=4)

    def update_plot(self):
        if self.df is None:
            return
        x_col = self.x_axis_combo.currentText()
        y_col = self.y_axis_combo.currentText()
        if not x_col or not y_col:
            return

        x, y, suitable_mask, valid_mask = self.build_mask(self.df, x_col, y_col)
        valid_df = self.df[valid_mask]

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_xscale("log")
        ax.set_yscale("log")

        group_colors = ["#7F8CFF", "#FF9F6E", "#8ED081", "#D68CFF", "#F2D16B"]
        for i, (gname, gdf) in enumerate(valid_df.groupby("group_name", dropna=False)):
            pts = np.column_stack((np.log10(pd.to_numeric(gdf[x_col])), np.log10(pd.to_numeric(gdf[y_col]))))
            patch = self.rounded_patch_from_log_points(pts, color=group_colors[i % len(group_colors)], alpha=0.22, lw=1.8, zorder=1)
            if patch is not None:
                ax.add_patch(patch)
                center = np.nanmedian(10 ** pts[:, 0]), np.nanmedian(10 ** pts[:, 1])
                ax.text(center[0], center[1], str(gname), fontsize=9, weight="bold", ha="center", va="center", zorder=5)

        for idx, row in valid_df.iterrows():
            is_ok = bool(suitable_mask.loc[idx])
            color = "#1976D2" if is_ok else "#9E9E9E"
            patch = self.material_patch(float(row[x_col]), float(row[y_col]), color=color)
            patch.set_alpha(0.9 if is_ok else 0.23)
            ax.add_patch(patch)

        cfg = self.current_condition_config()
        xx = np.logspace(np.log10(x[valid_mask].min()), np.log10(x[valid_mask].max()), 300)
        yy = 10 ** (cfg["m"] * np.log10(xx) + self.condition_intercept)
        self.line_artist = ax.plot(xx, yy, color="red", linewidth=2.6, label=f"Условие {cfg['label']}")[0]

        xmin = self.parse_optional_float(self.x_min_input)
        xmax = self.parse_optional_float(self.x_max_input)
        ymin = self.parse_optional_float(self.y_min_input)
        ymax = self.parse_optional_float(self.y_max_input)
        if xmin is not None:
            ax.axvline(xmin, color="#4CAF50", linestyle="--", linewidth=1.3)
        if xmax is not None:
            ax.axvline(xmax, color="#4CAF50", linestyle="--", linewidth=1.3)
        if ymin is not None:
            ax.axhline(ymin, color="#7E57C2", linestyle="--", linewidth=1.3)
        if ymax is not None:
            ax.axhline(ymax, color="#7E57C2", linestyle="--", linewidth=1.3)

        if any(v is not None for v in [xmin, xmax, ymin, ymax]):
            xlo = xmin if xmin is not None else x[valid_mask].min()
            xhi = xmax if xmax is not None else x[valid_mask].max()
            ylo = ymin if ymin is not None else y[valid_mask].min()
            yhi = ymax if ymax is not None else y[valid_mask].max()
            ax.fill_between([xlo, xhi], ylo, yhi, color="#00BCD4", alpha=0.08, zorder=0)

        suitable_df = self.df[suitable_mask].copy()
        self.last_suitable_df = suitable_df
        ax.text(
            0.98,
            0.98,
            f"Подходящих материалов: {len(suitable_df)}",
            transform=ax.transAxes,
            ha="right",
            va="top",
            fontsize=11,
            bbox=dict(facecolor="white", alpha=0.92, boxstyle="round,pad=0.3"),
        )

        line_val = cfg["from_b"](self.condition_intercept)
        self.info_label.setText(
            f"Материалов: {len(self.df)}\n"
            f"Подходящих: {len(suitable_df)}\n"
            f"Линия {cfg['label']} = {line_val:.4g}\n"
            f"(можно двигать мышью вверх/вниз и колесом)"
        )

        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        ax.set_title("Ashby диаграмма (логарифмический масштаб)")
        ax.grid(True, which="both", linestyle="--", alpha=0.3)
        ax.legend(loc="lower left")
        self.figure.tight_layout()
        self.canvas.draw_idle()

    def update_line_from_y(self, y_data, x_reference):
        if y_data is None or y_data <= 0 or x_reference <= 0:
            return
        cfg = self.current_condition_config()
        self.condition_intercept = np.log10(y_data) - cfg["m"] * np.log10(x_reference)
        self.update_plot()

    def on_press(self, event):
        if event.inaxes is None or self.line_artist is None:
            return
        contains, _ = self.line_artist.contains(event)
        if contains and event.button == 1:
            self.dragging_line = True

    def on_motion(self, event):
        if not self.dragging_line or event.inaxes is None:
            return
        xlim = event.inaxes.get_xlim()
        x_ref = np.sqrt(xlim[0] * xlim[1])
        self.update_line_from_y(event.ydata, x_ref)

    def on_release(self, event):
        self.dragging_line = False

    def on_scroll(self, event):
        if event.inaxes is None:
            return
        step = 0.04 if event.button == "up" else -0.04
        self.condition_intercept = (self.condition_intercept or 0.0) + step
        self.update_plot()

    def open_preview(self):
        if self.last_suitable_df is None or self.last_suitable_df.empty:
            QMessageBox.information(self, "Предпросмотр", "Подходящих материалов нет.")
            return

        preview_cols = [
            "material_name",
            "group_name",
            "subgroup_name",
            "Density_kg_m3",
            "Youngs_Modulus_GPa",
            "Strength_MPa",
            "E_over_rho",
            "Strength_over_rho",
            "SqrtE_over_rho",
        ]
        show_cols = [c for c in preview_cols if c in self.last_suitable_df.columns]

        dlg = QDialog(self)
        dlg.setWindowTitle("Предварительный просмотр подходящих материалов")
        dlg.resize(980, 560)
        layout = QVBoxLayout(dlg)

        table = QTableWidget()
        df = self.last_suitable_df[show_cols].reset_index(drop=True)
        table.setColumnCount(len(show_cols))
        table.setRowCount(len(df))
        table.setHorizontalHeaderLabels(show_cols)

        for r in range(len(df)):
            for c, col in enumerate(show_cols):
                table.setItem(r, c, QTableWidgetItem(str(df.iloc[r, c])))

        table.resizeColumnsToContents()
        layout.addWidget(table)
        dlg.exec_()


def main():
    app = QApplication(sys.argv)
    window = AshbyDiagramWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
