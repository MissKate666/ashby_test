import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.patches import Polygon as MplPolygon
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
from shapely.geometry import LineString, MultiPoint, Point, Polygon


class AshbyDiagramWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.df = None
        self.groups_df = None
        self.group_map = None
        self.dragging_line = False
        self.condition_intercept = None
        self.line_artist = None
        self.hover_annotation = None
        self.material_artists = []
        self.material_points = []
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
        self.condition_combo.addItems(["Не выбрано", "Лёгкость (E/ρ)", "Прочность (σ/ρ)", "Изгиб (√E/ρ)"])
        self.condition_combo.currentIndexChanged.connect(self.on_condition_changed)
        cond_layout.addRow("Критерий:", self.condition_combo)

        self.preference_combo = QComboBox()
        self.preference_combo.addItems(["Высокое значение", "Низкое значение"])
        self.preference_combo.currentIndexChanged.connect(self.update_plot)
        cond_layout.addRow("Подходит:", self.preference_combo)
        cond_group.setLayout(cond_layout)
        panel_layout.addWidget(cond_group)

        axis_group = QGroupBox("Диапазон по осям (опционально)")
        axis_layout = QGridLayout()
        self.x_min_input = QLineEdit()
        self.x_max_input = QLineEdit()
        self.y_min_input = QLineEdit()
        self.y_max_input = QLineEdit()
        for w in [self.x_min_input, self.x_max_input, self.y_min_input, self.y_max_input]:
            w.setPlaceholderText("пусто = без ограничения")
            w.editingFinished.connect(self.update_plot)

        axis_layout.addWidget(QLabel("X min"), 0, 0)
        axis_layout.addWidget(self.x_min_input, 0, 1)
        axis_layout.addWidget(QLabel("X max"), 1, 0)
        axis_layout.addWidget(self.x_max_input, 1, 1)
        axis_layout.addWidget(QLabel("Y min"), 2, 0)
        axis_layout.addWidget(self.y_min_input, 2, 1)
        axis_layout.addWidget(QLabel("Y max"), 3, 0)
        axis_layout.addWidget(self.y_max_input, 3, 1)
        axis_group.setLayout(axis_layout)
        panel_layout.addWidget(axis_group)

        self.preview_btn = QPushButton("Предварительный просмотр")
        self.preview_btn.clicked.connect(self.open_preview)
        panel_layout.addWidget(self.preview_btn)

        zoom_row = QHBoxLayout()
        self.zoom_in_btn = QPushButton("+")
        self.zoom_out_btn = QPushButton("-")
        self.zoom_in_btn.clicked.connect(lambda: self.zoom_plot(0.85))
        self.zoom_out_btn.clicked.connect(lambda: self.zoom_plot(1.18))
        zoom_row.addWidget(QLabel("Масштаб:"))
        zoom_row.addWidget(self.zoom_in_btn)
        zoom_row.addWidget(self.zoom_out_btn)
        panel_layout.addLayout(zoom_row)

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

            for frame, col in [(groups, "group_id"), (subgroups, "subgroup_id"), (subgroups, "group_id"), (materials, "subgroup_id")]:
                frame[col] = pd.to_numeric(frame[col], errors="coerce").astype("Int64")

            self.groups_df = groups.sort_values("group_id").reset_index(drop=True)
            merged = materials.merge(subgroups, on="subgroup_id", how="inner", validate="many_to_one")
            merged = merged.merge(groups, on="group_id", how="inner", validate="many_to_one")

            if merged["group_id"].isna().any() or merged["group_name"].isna().any():
                raise ValueError("Обнаружены материалы без группы после связывания таблиц.")

            found_groups = set(merged["group_id"].dropna().astype(int).unique().tolist())
            expected_groups = set(self.groups_df["group_id"].dropna().astype(int).tolist())
            if found_groups != expected_groups:
                missing = sorted(expected_groups - found_groups)
                raise ValueError(f"В диаграмме отсутствуют обязательные группы: {missing}")

            self.df = merged.reset_index(drop=True)

            self.on_condition_changed()
            self.info_label.setText(f"Загружено материалов: {len(self.df)}")
            self.update_plot()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные:\n{e}")

    def current_condition_config(self):
        idx = self.condition_combo.currentIndex()
        if idx == 1:
            return {"y_col": "Youngs_Modulus_GPa", "m": 1.0, "label": "E/ρ", "to_b": lambda v: np.log10(v), "from_b": lambda b: 10 ** b}
        if idx == 2:
            return {"y_col": "Strength_MPa", "m": 1.0, "label": "σ/ρ", "to_b": lambda v: np.log10(v), "from_b": lambda b: 10 ** b}
        if idx == 3:
            return {"y_col": "Youngs_Modulus_GPa", "m": 2.0, "label": "√E/ρ", "to_b": lambda v: 2 * np.log10(v), "from_b": lambda b: 10 ** (b / 2)}
        return None

    def on_condition_changed(self):
        cfg = self.current_condition_config()
        if cfg is None:
            self.condition_intercept = None
            self.update_plot()
            return
        if self.df is not None and len(self.df):
            if self.condition_combo.currentIndex() == 1:
                idx = pd.to_numeric(self.df["E_over_rho"], errors="coerce")
            elif self.condition_combo.currentIndex() == 2:
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

        if cfg is not None:
            if self.condition_intercept is None:
                ratios = ly - cfg["m"] * lx
                self.condition_intercept = float(np.nanmedian(ratios))
            line_vals = cfg["m"] * lx + self.condition_intercept
            high_side = self.preference_combo.currentIndex() == 0
            if high_side:
                cond_mask = ly >= line_vals
            else:
                cond_mask = ly <= line_vals
        else:
            cond_mask = pd.Series(True, index=lx.index)

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
        if len(points_log) == 0:
            return None

        if len(points_log) == 1:
            geom = Point(points_log[0])
            radius = 0.04
            rounded = geom.buffer(radius, join_style=1)
        elif len(points_log) == 2:
            geom = LineString(points_log)
            seg = np.linalg.norm(np.array(points_log[0]) - np.array(points_log[1]))
            radius = max(seg * 0.18, 0.03)
            rounded = geom.buffer(radius, cap_style=1, join_style=1)
        else:
            hull = MultiPoint(points_log).convex_hull
            if not isinstance(hull, Polygon):
                return None
            minx, miny, maxx, maxy = hull.bounds
            radius = max((maxx - minx), (maxy - miny)) * 0.14
            radius = max(radius, 0.02)
            rounded = hull.buffer(radius, join_style=1).buffer(-radius, join_style=1)

        if rounded.is_empty:
            return None
        if rounded.geom_type == "MultiPolygon":
            rounded = max(rounded.geoms, key=lambda g: g.area)
        coords = np.array(rounded.exterior.coords)
        coords_lin = np.column_stack((10 ** coords[:, 0], 10 ** coords[:, 1]))
        return MplPolygon(coords_lin, closed=True, facecolor=color, edgecolor=color, alpha=alpha, linewidth=lw, zorder=zorder)

    def material_patch(self, x, y, color="#1f77b4"):
        logx, logy = np.log10(x), np.log10(y)
        r = 0.018
        angles = np.linspace(0, 2 * np.pi, 7)[:-1]
        points = [(logx + r * np.cos(a), logy + r * np.sin(a)) for a in angles]
        poly = Polygon(points)
        rounded = poly.buffer(r * 0.55, join_style=1).buffer(-r * 0.55, join_style=1)
        coords = np.array(rounded.exterior.coords)
        coords_lin = np.column_stack((10 ** coords[:, 0], 10 ** coords[:, 1]))
        return MplPolygon(coords_lin, closed=True, facecolor=color, edgecolor="white", alpha=0.85, linewidth=0.5, zorder=4)

    def update_plot(self):
        if self.df is None:
            return
        x_col = "Density_kg_m3"
        cfg = self.current_condition_config()
        y_col = cfg["y_col"] if cfg is not None else "Youngs_Modulus_GPa"

        x, y, suitable_mask, valid_mask = self.build_mask(self.df, x_col, y_col)
        valid_df = self.df[valid_mask]

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_xscale("log")
        ax.set_yscale("log")
        self.material_artists = []
        self.material_points = []
        self.hover_annotation = None

        x_vals = pd.to_numeric(valid_df[x_col], errors="coerce")
        y_vals = pd.to_numeric(valid_df[y_col], errors="coerce")
        x_vals = x_vals[(x_vals > 0) & np.isfinite(x_vals)]
        y_vals = y_vals[(y_vals > 0) & np.isfinite(y_vals)]
        x_lo, x_hi = float(x_vals.min()), float(x_vals.max())
        y_lo, y_hi = float(y_vals.min()), float(y_vals.max())
        x_margin = 10 ** 0.16
        y_margin = 10 ** 0.16
        x_lim = (x_lo / x_margin, x_hi * x_margin)
        y_lim = (y_lo / y_margin, y_hi * y_margin)
        label_points = []
        group_bounds = []

        group_colors = ["#7F8CFF", "#FF9F6E", "#8ED081", "#D68CFF", "#F2D16B", "#5BB4FF", "#E798F2", "#A4DE6C"]
        subgroup_color = "#69A7FF"

        group_rows = self.groups_df.itertuples(index=False) if self.groups_df is not None else []
        for i, group_row in enumerate(group_rows):
            gname = group_row.group_name
            gid = group_row.group_id
            gdf = valid_df[valid_df["group_id"] == gid]
            if gdf.empty:
                continue
            group_ok = bool(suitable_mask.loc[gdf.index].any())
            group_alpha = 0.23 if group_ok else 0.08
            pts = np.column_stack((np.log10(pd.to_numeric(gdf[x_col])), np.log10(pd.to_numeric(gdf[y_col]))))
            patch = self.rounded_patch_from_log_points(
                pts,
                color=group_colors[i % len(group_colors)],
                alpha=group_alpha,
                lw=2.0 if group_ok else 1.0,
                zorder=0.5,
            )
            if patch is not None:
                ax.add_patch(patch)
                verts = patch.get_xy()
                group_bounds.append((verts[:, 0].min(), verts[:, 0].max(), verts[:, 1].min(), verts[:, 1].max()))
                center = np.nanmedian(10 ** pts[:, 0]), np.nanmedian(10 ** pts[:, 1])
                self.place_non_overlapping_label(
                    ax, center[0], center[1], str(gname), label_points, fontsize=9, weight="bold", alpha=0.95 if group_ok else 0.35, zorder=5
                )

        for sname, sdf in valid_df.groupby("subgroup_name", dropna=False):
            sub_ok = bool(suitable_mask.loc[sdf.index].any())
            sub_alpha = 0.2 if sub_ok else 0.06
            pts = np.column_stack((np.log10(pd.to_numeric(sdf[x_col])), np.log10(pd.to_numeric(sdf[y_col]))))
            spatch = self.rounded_patch_from_log_points(
                pts,
                color=subgroup_color,
                alpha=sub_alpha,
                lw=1.5 if sub_ok else 0.8,
                zorder=1.2,
            )
            if spatch is not None:
                ax.add_patch(spatch)
                s_center = np.nanmedian(10 ** pts[:, 0]), np.nanmedian(10 ** pts[:, 1])
                self.place_non_overlapping_label(
                    ax, s_center[0], s_center[1], str(sname), label_points, fontsize=7, weight="normal", alpha=0.8 if sub_ok else 0.35, zorder=5
                )

        for idx, row in valid_df.iterrows():
            is_ok = bool(suitable_mask.loc[idx])
            color = "#1976D2" if is_ok else "#9E9E9E"
            patch = self.material_patch(float(row[x_col]), float(row[y_col]), color=color)
            patch.set_alpha(0.9 if is_ok else 0.23)
            ax.add_patch(patch)
            self.material_artists.append((patch, str(row.get("material_name", "Material"))))
            self.material_points.append((float(row[x_col]), float(row[y_col]), str(row.get("material_name", "Material"))))

        if group_bounds:
            gx0 = min(b[0] for b in group_bounds)
            gx1 = max(b[1] for b in group_bounds)
            gy0 = min(b[2] for b in group_bounds)
            gy1 = max(b[3] for b in group_bounds)
            x_lim = (min(x_lim[0], gx0 / (10 ** 0.06)), max(x_lim[1], gx1 * (10 ** 0.06)))
            y_lim = (min(y_lim[0], gy0 / (10 ** 0.06)), max(y_lim[1], gy1 * (10 ** 0.06)))

        if cfg is not None:
            xx = np.logspace(np.log10(x_lim[0]), np.log10(x_lim[1]), 300)
            yy = 10 ** (cfg["m"] * np.log10(xx) + self.condition_intercept)
            self.line_artist = ax.plot(xx, yy, color="red", linewidth=2.6, label=f"Условие {cfg['label']}")[0]
        else:
            self.line_artist = None

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

        if cfg is not None and self.condition_intercept is not None:
            line_val = cfg["from_b"](self.condition_intercept)
            line_info = f"Линия {cfg['label']} = {line_val:.4g}\n(можно двигать мышью вверх/вниз и колесом)"
        else:
            line_info = "Условие пока не выбрано"
        self.info_label.setText(
            f"Материалов: {len(self.df)}\n"
            f"Подходящих: {len(suitable_df)}\n"
            f"{line_info}"
        )

        ax.set_xlim(*x_lim)
        ax.set_ylim(*y_lim)
        ax.set_xlabel("ρ — Density_kg_m3 (kg/m³)")
        if y_col == "Youngs_Modulus_GPa":
            ax.set_ylabel("E — Youngs_Modulus_GPa (GPa)")
        elif y_col == "Strength_MPa":
            ax.set_ylabel("σ — Strength_MPa (MPa)")
        else:
            ax.set_ylabel(y_col)
        ax.set_title("Ashby диаграмма (логарифмический масштаб)")
        ax.grid(True, which="both", linestyle="--", alpha=0.3)
        if self.line_artist is not None:
            ax.legend(loc="lower left")
        self.figure.subplots_adjust(left=0.08, right=0.98, top=0.93, bottom=0.1)
        self.canvas.draw_idle()

    def update_line_from_y(self, y_data, x_reference):
        if y_data is None or y_data <= 0 or x_reference <= 0:
            return
        cfg = self.current_condition_config()
        if cfg is None:
            return
        self.condition_intercept = np.log10(y_data) - cfg["m"] * np.log10(x_reference)
        self.update_plot()

    def on_press(self, event):
        if event.inaxes is None or self.line_artist is None:
            return
        contains, _ = self.line_artist.contains(event)
        if contains and event.button == 1:
            self.dragging_line = True

    def on_motion(self, event):
        if event.inaxes is None:
            return
        if self.dragging_line:
            xlim = event.inaxes.get_xlim()
            x_ref = np.sqrt(xlim[0] * xlim[1])
            self.update_line_from_y(event.ydata, x_ref)
            return
        self.update_material_hover(event)

    def on_release(self, event):
        self.dragging_line = False

    def on_scroll(self, event):
        if event.inaxes is None:
            return
        step = 0.04 if event.button == "up" else -0.04
        self.condition_intercept = (self.condition_intercept or 0.0) + step
        self.update_plot()

    def update_material_hover(self, event):
        if self.hover_annotation is None:
            self.hover_annotation = event.inaxes.annotate(
                "",
                xy=(0, 0),
                xytext=(10, 10),
                textcoords="offset points",
                bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.9),
                fontsize=8,
            )
            self.hover_annotation.set_visible(False)

        found = False
        for patch, name in self.material_artists:
            contains, _ = patch.contains(event)
            if contains:
                self.hover_annotation.xy = (event.xdata, event.ydata)
                self.hover_annotation.set_text(name)
                self.hover_annotation.set_visible(True)
                found = True
                break
        if not found and event.xdata and event.ydata and self.material_points:
            lx, ly = np.log10(event.xdata), np.log10(event.ydata)
            nearest = min(
                self.material_points,
                key=lambda p: (np.log10(p[0]) - lx) ** 2 + (np.log10(p[1]) - ly) ** 2,
            )
            dist = ((np.log10(nearest[0]) - lx) ** 2 + (np.log10(nearest[1]) - ly) ** 2) ** 0.5
            if dist < 0.06:
                self.hover_annotation.xy = (nearest[0], nearest[1])
                self.hover_annotation.set_text(nearest[2])
                self.hover_annotation.set_visible(True)
                found = True
        if not found and self.hover_annotation.get_visible():
            self.hover_annotation.set_visible(False)
        self.canvas.draw_idle()

    def place_non_overlapping_label(self, ax, x, y, text, existing_points, fontsize=8, weight="normal", alpha=0.8, zorder=5):
        lx, ly = np.log10(x), np.log10(y)
        min_dist = 0.08
        tries = 0
        while tries < 7 and any(np.hypot(lx - ex, ly - ey) < min_dist for ex, ey in existing_points):
            ly += 0.035
            tries += 1
        existing_points.append((lx, ly))
        ax.text(10 ** lx, 10 ** ly, text, fontsize=fontsize, weight=weight, ha="center", va="center", alpha=alpha, zorder=zorder)

    def zoom_plot(self, factor):
        if self.figure.axes:
            ax = self.figure.axes[0]
            x0, x1 = ax.get_xlim()
            y0, y1 = ax.get_ylim()
            cx = np.sqrt(x0 * x1)
            cy = np.sqrt(y0 * y1)
            hx = (np.log10(x1) - np.log10(x0)) * 0.5 * factor
            hy = (np.log10(y1) - np.log10(y0)) * 0.5 * factor
            ax.set_xlim(10 ** (np.log10(cx) - hx), 10 ** (np.log10(cx) + hx))
            ax.set_ylim(10 ** (np.log10(cy) - hy), 10 ** (np.log10(cy) + hy))
            self.canvas.draw_idle()

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
