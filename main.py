import sys
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
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
    QHeaderView,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QListWidget,
    QListWidgetItem,
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
        self.dragging_line = None
        self.condition_intercepts = {}
        self.line_artists = []
        self.hover_annotation = None
        self.material_artists = []
        self.material_points = []
        self.panning = False
        self.pan_start = None
        self.invalid_bounds_notified = False
        self.translator = self.build_translator()
        self.translation_cache = {}
        self.translation_overrides = {
            "Glasses": "Стекло",
            "Natural": "Природные",
        }
        self.last_suitable_df = pd.DataFrame()
        self.last_suitable_by_criterion = {}
        self.group_colors = ["#003F88", "#D90429", "#2B9348", "#FFBA08", "#111111", "#00B4D8", "#F72585", "#FB5607", "#70E000", "#8338EC"]
        self.default_paths = {
            "groups": Path("materials_for_project/Group_materials.csv"),
            "subgroups": Path("materials_for_project/Subgroup_materials.csv"),
            "materials": Path("materials_for_project/Dataset_for_Ashby.csv"),
        }
        self.init_ui()
        self.load_default_data()

    def init_ui(self):
        self.setWindowTitle("Селектор Эшби")
        self.setGeometry(100, 80, 1450, 900)
        self.setFocusPolicy(Qt.StrongFocus)
        self.apply_modern_theme()

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(16)

        panel = QWidget()
        panel.setObjectName("controlPanel")
        panel.setMaximumWidth(360)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(16, 16, 16, 16)
        panel_layout.setSpacing(12)

        cond_group = QGroupBox("Условия")
        cond_layout = QFormLayout()
        self.criteria_list = QListWidget()
        self.criteria_list.setSelectionMode(QListWidget.NoSelection)
        for key, cfg in self.condition_configs().items():
            item = QListWidgetItem(cfg["title"])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            item.setData(Qt.UserRole, key)
            self.criteria_list.addItem(item)
        self.criteria_list.itemChanged.connect(self.on_criteria_changed)
        cond_layout.addRow("Критерии:", self.criteria_list)

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
        self.preview_btn.setObjectName("primaryButton")
        self.preview_btn.clicked.connect(self.open_preview)
        panel_layout.addWidget(self.preview_btn)

        self.info_label = QLabel("Данные не загружены")
        self.info_label.setWordWrap(True)
        panel_layout.addWidget(self.info_label)
        self.group_legend_label = QLabel("Цвета групп появятся после загрузки данных")
        self.group_legend_label.setWordWrap(True)
        self.group_legend_label.setStyleSheet("font-size: 15px; font-weight: 700; color: #1E293B;")
        panel_layout.addWidget(self.group_legend_label)
        self.group_legend_widget = QWidget()
        self.group_legend_layout = QVBoxLayout(self.group_legend_widget)
        self.group_legend_layout.setContentsMargins(0, 0, 0, 0)
        self.group_legend_layout.setSpacing(8)
        panel_layout.addWidget(self.group_legend_widget)
        panel_layout.addStretch(1)

        plot_panel = QWidget()
        plot_panel.setObjectName("plotPanel")
        plot_layout = QVBoxLayout(plot_panel)
        plot_layout.setContentsMargins(18, 16, 18, 16)
        plot_layout.setSpacing(10)
        zoom_row = QHBoxLayout()
        self.zoom_in_btn = QPushButton("+")
        self.zoom_out_btn = QPushButton("-")
        self.zoom_in_btn.clicked.connect(lambda: self.zoom_plot(0.85))
        self.zoom_out_btn.clicked.connect(lambda: self.zoom_plot(1.18))
        zoom_row.addWidget(QLabel("Масштаб:"))
        zoom_row.addWidget(self.zoom_in_btn)
        zoom_row.addWidget(self.zoom_out_btn)
        zoom_row.addStretch(1)
        plot_layout.addLayout(zoom_row)
        self.counter_label = QLabel("Подходящих материалов: 0")
        self.counter_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        plot_layout.addWidget(self.counter_label, alignment=Qt.AlignHCenter)
        self.figure = plt.figure(facecolor="#F8FAFC")
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background: #F8FAFC; border-radius: 12px;")
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.canvas.updateGeometry()
        plot_layout.addWidget(self.canvas)
        plot_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        main_layout.addWidget(panel)
        main_layout.addWidget(plot_panel, stretch=1)

        self.canvas.mpl_connect("button_press_event", self.on_press)
        self.canvas.mpl_connect("button_release_event", self.on_release)
        self.canvas.mpl_connect("motion_notify_event", self.on_motion)
        self.canvas.mpl_connect("scroll_event", self.on_scroll)

    def apply_modern_theme(self):
        self.setStyleSheet(
            """
            QWidget {
                background-color: #F3F6FB;
                color: #1F2937;
                font-size: 13px;
                font-family: "Segoe UI", "Inter", "Roboto", sans-serif;
            }
            #controlPanel, #plotPanel {
                background: #FFFFFF;
                border: 1px solid #E5EAF2;
                border-radius: 14px;
            }
            QGroupBox {
                font-weight: 600;
                border: 1px solid #E5EAF2;
                border-radius: 10px;
                margin-top: 10px;
                padding: 10px 8px 8px 8px;
                background: #FCFDFF;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
                color: #334155;
            }
            QLineEdit, QComboBox {
                border: 1px solid #D6DCE8;
                border-radius: 8px;
                padding: 6px 8px;
                background: #FFFFFF;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #4C6EF5;
            }
            QPushButton {
                border: 1px solid #D6DCE8;
                border-radius: 8px;
                padding: 7px 10px;
                background: #FFFFFF;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #F1F5FF;
            }
            QPushButton:pressed {
                background: #E4ECFF;
            }
            QPushButton#primaryButton {
                background: #3B5BDB;
                border-color: #3B5BDB;
                color: #FFFFFF;
            }
            QPushButton#primaryButton:hover {
                background: #2F4FCB;
            }
            QLabel {
                background: transparent;
            }
            #controlPanel QLabel,
            #controlPanel QGroupBox,
            #controlPanel QComboBox,
            #controlPanel QLineEdit,
            #controlPanel QPushButton {
                font-size: 15px;
            }
            """
        )

    @staticmethod
    def lighten_color(hex_color, factor=0.65):
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        r = int(r + (255 - r) * factor)
        g = int(g + (255 - g) * factor)
        b = int(b + (255 - b) * factor)
        return f"#{r:02X}{g:02X}{b:02X}"

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

            if self.translator is None:
                raise RuntimeError("Не удалось инициализировать библиотеку перевода. Проверьте подключение к интернету и доступ к pip.")

            self.groups_df["group_name"] = self.translate_series_to_russian(self.groups_df["group_name"])
            for col in ["group_name", "subgroup_name", "material_name"]:
                if col in merged.columns:
                    merged[col] = self.translate_series_to_russian(merged[col])

            self.df = merged.reset_index(drop=True)
            self.info_label.setText(f"Загружено материалов: {len(self.df)}")
            self.update_group_legend()
            self.clear_plot_placeholder("Выберите критерий, чтобы построить диаграмму")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные:\n{e}")

    def update_group_legend(self):
        if self.groups_df is None or self.groups_df.empty:
            self.group_legend_label.setText("Цвета групп недоступны")
            return
        self.group_legend_label.setText("Цвета групп:")
        while self.group_legend_layout.count():
            item = self.group_legend_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        for i, row in enumerate(self.groups_df.itertuples(index=False)):
            color = self.group_colors[i % len(self.group_colors)]
            chip = QLabel(f"<span style='color:{color}; font-size:24px;'>●</span>  {row.group_name}")
            chip.setStyleSheet(
                "background: #F8FAFF; border: 1px solid #D8E1F2; border-radius: 10px; "
                "padding: 8px 10px; color: #1E293B; font-size: 15px; font-weight: 600;"
            )
            self.group_legend_layout.addWidget(chip)

    def clear_plot_placeholder(self, message):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor("#F8FAFC")
        ax.axis("off")
        ax.text(0.5, 0.5, message, ha="center", va="center", fontsize=12, color="#666666", transform=ax.transAxes)
        self.counter_label.setText("Подходящих материалов: 0")
        self.last_suitable_df = pd.DataFrame()
        self.last_suitable_by_criterion = {}
        self.canvas.draw_idle()

    @staticmethod
    def condition_configs():
        return {
            "lightness": {"title": "Лёгкость (E/ρ)", "ratio_col": "E_over_rho", "y_col": "Youngs_Modulus_GPa", "m": 1.0, "label": "E/ρ", "to_b": lambda v: np.log10(v), "from_b": lambda b: 10 ** b},
            "strength": {"title": "Прочность (σ/ρ)", "ratio_col": "Strength_over_rho", "y_col": "Strength_MPa", "m": 1.0, "label": "σ/ρ", "to_b": lambda v: np.log10(v), "from_b": lambda b: 10 ** b},
            "bend": {"title": "Изгиб (√E/ρ)", "ratio_col": "SqrtE_over_rho", "y_col": "Youngs_Modulus_GPa", "m": 2.0, "label": "√E/ρ", "to_b": lambda v: 2 * np.log10(v), "from_b": lambda b: 10 ** (b / 2)},
        }

    def selected_condition_keys(self):
        keys = []
        for i in range(self.criteria_list.count()):
            item = self.criteria_list.item(i)
            if item.checkState() == Qt.Checked:
                keys.append(item.data(Qt.UserRole))
        return keys

    def on_criteria_changed(self, _item=None):
        selected = set(self.selected_condition_keys())
        for key in list(self.condition_intercepts.keys()):
            if key not in selected:
                self.condition_intercepts.pop(key, None)

        if self.df is not None and len(self.df):
            cfg_map = self.condition_configs()
            for key in selected:
                if key in self.condition_intercepts:
                    continue
                cfg = cfg_map[key]
                idx = pd.to_numeric(self.df[cfg["ratio_col"]], errors="coerce")
                idx = idx[(idx > 0) & np.isfinite(idx)]
                if len(idx):
                    self.condition_intercepts[key] = cfg["to_b"](float(idx.median()))
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

    def translate_series_to_russian(self, series: pd.Series) -> pd.Series:
        if self.translator is None:
            return series

        def translate_value(value):
            if pd.isna(value):
                return value
            text = str(value).strip()
            if not text:
                return value
            if text in self.translation_overrides:
                return self.translation_overrides[text]
            if text in self.translation_cache:
                return self.translation_cache[text]
            try:
                translated = self.translator.translate(text)
                self.translation_cache[text] = translated if translated else text
                return self.translation_cache[text]
            except Exception:
                self.translation_cache[text] = text
                return text

        return series.map(translate_value)

    def build_translator(self):
        translator = self.build_deep_translator()
        if translator is not None:
            return translator
        return self.build_googletrans_translator()

    @staticmethod
    def install_package(package_name):
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", package_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception:
            return False

    def build_deep_translator(self):
        try:
            from deep_translator import GoogleTranslator, MyMemoryTranslator
        except ImportError:
            if not self.install_package("deep-translator"):
                return None
            try:
                from deep_translator import GoogleTranslator, MyMemoryTranslator
            except Exception:
                return None

        backends = [
            GoogleTranslator(source="auto", target="ru"),
            MyMemoryTranslator(source="en-US", target="ru-RU"),
        ]
        for backend in backends:
            try:
                if backend.translate("Steel"):
                    return backend
            except Exception:
                continue
        return None

    def build_googletrans_translator(self):
        try:
            from googletrans import Translator as GoogleTransTranslator
        except ImportError:
            if not self.install_package("googletrans==4.0.0-rc1"):
                return None
            try:
                from googletrans import Translator as GoogleTransTranslator
            except Exception:
                return None

        class GoogleTransAdapter:
            def __init__(self):
                self.translator = GoogleTransTranslator()

            def translate(self, text):
                return self.translator.translate(text, dest="ru").text

        try:
            adapter = GoogleTransAdapter()
            if adapter.translate("Steel"):
                return adapter
        except Exception:
            return None
        return None

    def validate_axis_bounds(self):
        xmin = self.parse_optional_float(self.x_min_input)
        xmax = self.parse_optional_float(self.x_max_input)
        ymin = self.parse_optional_float(self.y_min_input)
        ymax = self.parse_optional_float(self.y_max_input)

        errors = []
        if xmin is not None and xmax is not None and xmin > xmax:
            errors.append("X min не может быть больше X max.")
        if ymin is not None and ymax is not None and ymin > ymax:
            errors.append("Y min не может быть больше Y max.")

        if errors:
            if not self.invalid_bounds_notified:
                QMessageBox.warning(self, "Некорректные границы осей", "\n".join(errors))
                self.invalid_bounds_notified = True
            return None

        self.invalid_bounds_notified = False
        return xmin, xmax, ymin, ymax

    def build_mask(self, df, x_col, y_col, condition_keys):
        x = pd.to_numeric(df[x_col], errors="coerce")
        y = pd.to_numeric(df[y_col], errors="coerce")
        mask = (x > 0) & (y > 0) & np.isfinite(x) & np.isfinite(y)

        lx = np.log10(x[mask])
        ly = np.log10(y[mask])

        cond_mask = pd.Series(True, index=lx.index)
        cfg_map = self.condition_configs()
        for key in condition_keys:
            cfg = cfg_map[key]
            b = self.condition_intercepts.get(key)
            if b is None:
                continue
            line_vals = cfg["m"] * lx + b
            high_side = self.preference_combo.currentIndex() == 0
            cond_mask &= (ly >= line_vals) if high_side else (ly <= line_vals)

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

    def rounded_geometry_from_log_points(self, points_log, padding=0.0):
        if len(points_log) == 0:
            return None

        smooth_radius = 0.02
        if len(points_log) == 1:
            geom = Point(points_log[0])
            radius = 0.055
            rounded = geom.buffer(radius + padding, join_style=1)
        elif len(points_log) == 2:
            geom = LineString(points_log)
            seg = np.linalg.norm(np.array(points_log[0]) - np.array(points_log[1]))
            radius = max(seg * 0.24, 0.045)
            rounded = geom.buffer(radius + padding, cap_style=1, join_style=1)
        else:
            hull = MultiPoint(points_log).convex_hull
            if not isinstance(hull, Polygon):
                return None
            minx, miny, maxx, maxy = hull.bounds
            radius = max((maxx - minx), (maxy - miny)) * 0.2
            radius = max(radius, 0.035)
            rounded = hull.buffer(radius + padding, join_style=1).buffer(-radius, join_style=1)
            smooth_radius = radius * 0.35

        if rounded.is_empty:
            return None
        rounded = rounded.buffer(smooth_radius, join_style=1).buffer(-smooth_radius, join_style=1)
        if rounded.is_empty:
            return None
        if rounded.geom_type == "MultiPolygon":
            rounded = max(rounded.geoms, key=lambda g: g.area)
        return rounded

    def rounded_patch_from_log_points(self, points_log, color, alpha, lw=1.2, zorder=2):
        rounded = self.rounded_geometry_from_log_points(points_log)
        if rounded is None:
            return None
        return self.geometry_to_patch(rounded, color=color, alpha=alpha, lw=lw, zorder=zorder)

    def geometry_to_patch(self, geom, color, alpha, lw=1.2, zorder=2):
        if geom is None or geom.is_empty:
            return None
        if geom.geom_type == "MultiPolygon":
            geom = max(geom.geoms, key=lambda g: g.area)
        if geom.geom_type != "Polygon":
            return None
        minx, miny, maxx, maxy = geom.bounds
        rounding = max(maxx - minx, maxy - miny) * 0.03
        if rounding > 0:
            geom = geom.buffer(rounding, join_style=1).buffer(-rounding, join_style=1)
            if geom.is_empty:
                return None
            if geom.geom_type == "MultiPolygon":
                geom = max(geom.geoms, key=lambda g: g.area)
        coords = np.array(geom.exterior.coords)
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
        limits = self.validate_axis_bounds()
        if limits is None:
            return

        condition_keys = self.selected_condition_keys()
        if not condition_keys:
            self.clear_plot_placeholder("Выберите хотя бы один критерий")
            return

        x_col = "Density_kg_m3"
        cfg_map = self.condition_configs()
        y_cols = [cfg_map[k]["y_col"] for k in condition_keys]
        mask_y_col = "Strength_MPa" if "Strength_MPa" in y_cols else "Youngs_Modulus_GPa"

        _, _, suitable_mask, _ = self.build_mask(self.df, x_col, mask_y_col, condition_keys)
        self.last_suitable_by_criterion = {}

        self.figure.clear()
        axes = self.figure.subplots(1, len(condition_keys), squeeze=False)[0]
        self.material_artists = []
        self.material_points = []
        self.hover_annotation = None
        self.line_artists = []

        for ax, key in zip(axes, condition_keys):
            cfg = cfg_map[key]
            y_col = cfg["y_col"]
            _, _, criterion_mask, criterion_valid_mask = self.build_mask(self.df, x_col, y_col, [key])
            criterion_df = self.df[criterion_valid_mask]
            self.last_suitable_by_criterion[key] = self.df[criterion_mask].copy()

            xvals = pd.to_numeric(criterion_df[x_col], errors="coerce")
            yvals = pd.to_numeric(criterion_df[y_col], errors="coerce")
            pair_mask = (xvals > 0) & (yvals > 0) & np.isfinite(xvals) & np.isfinite(yvals)
            pair_df = criterion_df[pair_mask]

            ax.set_facecolor("#F8FAFC")
            ax.set_xscale("log")
            ax.set_yscale("log")

            if pair_df.empty:
                ax.text(0.5, 0.5, "Нет данных", transform=ax.transAxes, ha="center", va="center")
                continue

            x_vals = pd.to_numeric(pair_df[x_col], errors="coerce")
            y_vals = pd.to_numeric(pair_df[y_col], errors="coerce")
            x_lo, x_hi = float(x_vals.min()), float(x_vals.max())
            y_lo, y_hi = float(y_vals.min()), float(y_vals.max())
            x_margin = 10 ** 0.16
            y_margin = 10 ** 0.16
            x_lim = (x_lo / x_margin, x_hi * x_margin)
            y_lim = (y_lo / y_margin, y_hi * y_margin)
            group_bounds = []

            group_color_by_id = {}
            group_geom_by_id = {}
            group_patch_by_id = {}
            group_rows = self.groups_df.itertuples(index=False) if self.groups_df is not None else []
            for i, group_row in enumerate(group_rows):
                gid = group_row.group_id
                group_color_by_id[gid] = self.group_colors[i % len(self.group_colors)]
                gdf = pair_df[pair_df["group_id"] == gid]
                if gdf.empty:
                    continue
                group_ok = bool(criterion_mask.loc[gdf.index].any())
                group_alpha = 0.23 if group_ok else 0.08
                pts = np.column_stack((np.log10(pd.to_numeric(gdf[x_col])), np.log10(pd.to_numeric(gdf[y_col]))))
                ggeom = self.rounded_geometry_from_log_points(pts, padding=0.028)
                group_geom_by_id[gid] = ggeom
                patch = self.geometry_to_patch(ggeom, color=group_color_by_id[gid], alpha=group_alpha, lw=2.0 if group_ok else 1.0, zorder=0.5)
                if patch is not None:
                    ax.add_patch(patch)
                    group_patch_by_id[gid] = patch
                    verts = patch.get_xy()
                    group_bounds.append((verts[:, 0].min(), verts[:, 0].max(), verts[:, 1].min(), verts[:, 1].max()))

            for _, sdf in pair_df.groupby("subgroup_name", dropna=False):
                sub_ok = bool(criterion_mask.loc[sdf.index].any())
                sub_alpha = 0.2 if sub_ok else 0.06
                pts = np.column_stack((np.log10(pd.to_numeric(sdf[x_col])), np.log10(pd.to_numeric(sdf[y_col]))))
                subgroup_group_id = sdf["group_id"].iloc[0] if len(sdf) else None
                base_group_color = group_color_by_id.get(subgroup_group_id, "#3B5BDB")
                subgroup_color = self.lighten_color(base_group_color, factor=0.68)
                sgeom = self.rounded_geometry_from_log_points(pts)
                ggeom = group_geom_by_id.get(subgroup_group_id)
                if sgeom is not None and ggeom is not None:
                    sgeom = sgeom.intersection(ggeom)
                spatch = self.geometry_to_patch(sgeom, color=subgroup_color, alpha=sub_alpha, lw=1.5 if sub_ok else 0.8, zorder=1.2)
                if spatch is not None:
                    ax.add_patch(spatch)

            for idx, row in pair_df.iterrows():
                is_ok = bool(criterion_mask.loc[idx])
                patch = self.material_patch(float(row[x_col]), float(row[y_col]), color="#000000")
                group_patch = group_patch_by_id.get(row.get("group_id"))
                if group_patch is not None:
                    patch.set_clip_path(group_patch)
                patch.set_alpha(0.9 if is_ok else 0.2)
                ax.add_patch(patch)

            if group_bounds:
                gx0 = min(b[0] for b in group_bounds)
                gx1 = max(b[1] for b in group_bounds)
                gy0 = min(b[2] for b in group_bounds)
                gy1 = max(b[3] for b in group_bounds)
                x_lim = (min(x_lim[0], gx0 / (10 ** 0.06)), max(x_lim[1], gx1 * (10 ** 0.06)))
                y_lim = (min(y_lim[0], gy0 / (10 ** 0.06)), max(y_lim[1], gy1 * (10 ** 0.06)))

            b = self.condition_intercepts.get(key)
            if b is not None:
                xx = np.logspace(np.log10(x_lim[0]), np.log10(x_lim[1]), 300)
                yy = 10 ** (cfg["m"] * np.log10(xx) + b)
                line = ax.plot(xx, yy, color="#E03131", linewidth=2.6, label=f"Условие {cfg['label']}")[0]
                self.line_artists.append((key, ax, line))

            ax.set_xlim(*x_lim)
            ax.set_ylim(*y_lim)
            ax.set_xlabel("ρ — Плотность (кг/м³)", fontsize=10, color="#334155")
            ax.set_ylabel("E — Модуль Юнга (ГПа)" if y_col == "Youngs_Modulus_GPa" else "σ — Прочность (МПа)", fontsize=10, color="#334155")
            ax.set_title(f"Диаграмма Эшби: {cfg['label']}", fontsize=12, pad=12, color="#0F172A", weight="semibold")
            criterion_count = int(criterion_mask.sum())
            ax.text(
                0.5,
                1.01,
                f"Подходящих материалов: {criterion_count}",
                transform=ax.transAxes,
                ha="center",
                va="bottom",
                fontsize=10,
                color="#0F172A",
                weight="semibold",
            )
            ax.tick_params(axis="both", which="major", labelsize=9, colors="#475569")
            for spine in ax.spines.values():
                spine.set_color("#CBD5E1")
            ax.grid(True, which="major", linestyle="-", linewidth=0.8, alpha=0.38, color="#CBD5E1")
            ax.grid(True, which="minor", linestyle="--", linewidth=0.55, alpha=0.22, color="#DCE3EE")
            if b is not None:
                ax.legend(loc="lower left")

        suitable_df = self.df[suitable_mask].copy()
        self.last_suitable_df = suitable_df
        self.counter_label.setText(f"Подходящих материалов: {len(suitable_df)}")
        self.info_label.setText(
            f"Материалов: {len(self.df)}\n"
            f"Подходящих: {len(suitable_df)}\n"
            "Линии критериев синхронизированы между диаграммами"
        )

        self.figure.subplots_adjust(left=0.05, right=0.99, top=0.93, bottom=0.12, wspace=0.2)
        self.canvas.draw_idle()

    def update_line_from_y(self, criterion_key, y_data, x_reference):
        if y_data is None or y_data <= 0 or x_reference <= 0:
            return
        cfg = self.condition_configs()[criterion_key]
        old_b = self.condition_intercepts.get(criterion_key)
        if old_b is None:
            return
        new_b = np.log10(y_data) - cfg["m"] * np.log10(x_reference)
        delta = new_b - old_b
        for key in self.selected_condition_keys():
            if key in self.condition_intercepts:
                self.condition_intercepts[key] += delta
        self.update_plot()

    def on_press(self, event):
        if event.button == 2 and event.inaxes is not None:
            self.panning = True
            self.pan_start = (event.xdata, event.ydata, event.inaxes.get_xlim(), event.inaxes.get_ylim())
            return
        if event.inaxes is None or not self.line_artists:
            return
        for key, ax, line in self.line_artists:
            if ax is not event.inaxes:
                continue
            contains, _ = line.contains(event)
            if contains and event.button == 1:
                self.dragging_line = key
                break

    def on_motion(self, event):
        if event.inaxes is None:
            return
        if self.dragging_line:
            xlim = event.inaxes.get_xlim()
            x_ref = np.sqrt(xlim[0] * xlim[1])
            self.update_line_from_y(self.dragging_line, event.ydata, x_ref)
            return
        if self.panning and self.pan_start is not None:
            start_x, start_y, xlim0, ylim0 = self.pan_start
            if start_x and start_y and start_x > 0 and start_y > 0 and event.xdata and event.ydata:
                dx = np.log10(event.xdata) - np.log10(start_x)
                dy = np.log10(event.ydata) - np.log10(start_y)
                new_xlim = (10 ** (np.log10(xlim0[0]) - dx), 10 ** (np.log10(xlim0[1]) - dx))
                new_ylim = (10 ** (np.log10(ylim0[0]) - dy), 10 ** (np.log10(ylim0[1]) - dy))
                event.inaxes.set_xlim(*new_xlim)
                event.inaxes.set_ylim(*new_ylim)
                self.canvas.draw_idle()
            return
        self.update_material_hover(event)

    def on_release(self, event):
        self.dragging_line = None
        self.panning = False
        self.pan_start = None

    def on_scroll(self, event):
        if event.inaxes is None:
            return
        self.zoom_plot(0.88 if event.button == "up" else 1.14)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Up:
            self.shift_condition_line(+0.04)
            event.accept()
            return
        if event.key() == Qt.Key_Down:
            self.shift_condition_line(-0.04)
            event.accept()
            return
        super().keyPressEvent(event)

    def shift_condition_line(self, step):
        selected = self.selected_condition_keys()
        if not selected:
            return
        for key in selected:
            self.condition_intercepts[key] = self.condition_intercepts.get(key, 0.0) + step
        self.update_plot()

    def update_material_hover(self, event):
        if self.hover_annotation is None:
            self.hover_annotation = event.inaxes.annotate(
                "",
                xy=(0, 0),
                xytext=(14, 14),
                textcoords="offset points",
                bbox=dict(boxstyle="round,pad=0.55", fc="white", alpha=0.96, ec="#CBD5E1", lw=1.0),
                fontsize=11,
                zorder=30,
            )
            self.hover_annotation.set_clip_on(False)
            self.hover_annotation.set_visible(False)

        found = False
        for patch, name in self.material_artists:
            contains, _ = patch.contains(event)
            if contains:
                self.hover_annotation.xy = (event.xdata, event.ydata)
                self.hover_annotation.set_text(name)
                self.hover_annotation.set_visible(True)
                self.adjust_hover_position(event, name)
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
                self.adjust_hover_position(event, nearest[2])
                found = True
        if not found and self.hover_annotation.get_visible():
            self.hover_annotation.set_visible(False)
        self.canvas.draw_idle()

    def adjust_hover_position(self, event, text):
        ax = event.inaxes
        if ax is None:
            return
        lines = max(1, text.count("\n") + 1)
        dx = 14
        dy = 14 if event.y < (ax.bbox.y0 + ax.bbox.y1) / 2 else -(22 + lines * 6)
        self.hover_annotation.set_position((dx, dy))

        renderer = self.canvas.get_renderer()
        if renderer is None:
            return
        ann_box = self.hover_annotation.get_window_extent(renderer=renderer)
        bounds = ax.bbox
        pad = 6
        shift_x = 0
        shift_y = 0

        if ann_box.x1 > bounds.x1 - pad:
            shift_x = (bounds.x1 - pad) - ann_box.x1
        elif ann_box.x0 < bounds.x0 + pad:
            shift_x = (bounds.x0 + pad) - ann_box.x0

        if ann_box.y1 > bounds.y1 - pad:
            shift_y = (bounds.y1 - pad) - ann_box.y1
        elif ann_box.y0 < bounds.y0 + pad:
            shift_y = (bounds.y0 + pad) - ann_box.y0

        if shift_x or shift_y:
            ox, oy = self.hover_annotation.get_position()
            to_pt = 72.0 / self.figure.dpi
            self.hover_annotation.set_position((ox + shift_x * to_pt, oy + shift_y * to_pt))

    def place_non_overlapping_label(self, ax, x, y, text, existing_points, fontsize=8, weight="normal", alpha=0.8, zorder=5):
        anchor_px = ax.transData.transform((x, y))
        candidate_offsets = [
            (0, 0), (0, 14), (0, -14), (14, 0), (-14, 0),
            (12, 12), (-12, 12), (12, -12), (-12, -12),
            (0, 24), (24, 0), (-24, 0), (0, -24),
        ]
        min_dist_px = max(48, fontsize * 5)

        best_offset = candidate_offsets[0]
        best_score = -1
        for dx, dy in candidate_offsets:
            px = (anchor_px[0] + dx, anchor_px[1] + dy)
            if not existing_points:
                best_offset = (dx, dy)
                break
            dist = min(np.hypot(px[0] - ex, px[1] - ey) for ex, ey in existing_points)
            if dist > min_dist_px:
                best_offset = (dx, dy)
                break
            if dist > best_score:
                best_score = dist
                best_offset = (dx, dy)

        final_px = (anchor_px[0] + best_offset[0], anchor_px[1] + best_offset[1])
        existing_points.append(final_px)
        txt = ax.annotate(
            text,
            xy=(x, y),
            xytext=best_offset,
            textcoords="offset points",
            fontsize=fontsize,
            weight=weight,
            ha="center",
            va="center",
            alpha=alpha,
            color="#0F172A",
            zorder=zorder,
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.72 if alpha > 0.6 else 0.45),
        )
        txt.set_path_effects([pe.withStroke(linewidth=1.6, foreground="white", alpha=0.9)])

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
        selected_keys = self.selected_condition_keys()
        if not selected_keys:
            QMessageBox.information(self, "Предпросмотр", "Сначала выберите критерии.")
            return

        if not self.last_suitable_by_criterion or all(self.last_suitable_by_criterion.get(k, pd.DataFrame()).empty for k in selected_keys):
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
        col_titles_ru = {
            "material_name": "Материал",
            "group_name": "Группа",
            "subgroup_name": "Подгруппа",
            "Density_kg_m3": "Плотность, кг/м³",
            "Youngs_Modulus_GPa": "Модуль Юнга, ГПа",
            "Strength_MPa": "Прочность, МПа",
            "E_over_rho": "E/ρ",
            "Strength_over_rho": "σ/ρ",
            "SqrtE_over_rho": "√E/ρ",
        }

        dlg = QDialog(self)
        dlg.setWindowTitle("Предварительный просмотр подходящих материалов")
        dlg.resize(980, 560)
        layout = QVBoxLayout(dlg)

        table = QTableWidget()
        table_style = (
            """
            QTableWidget {
                background: #FFFFFF;
                border: 1px solid #E5EAF2;
                gridline-color: #EEF2F7;
                alternate-background-color: #F8FAFD;
            }
            QHeaderView::section {
                background: #EEF3FF;
                color: #1E293B;
                padding: 6px;
                border: none;
                border-right: 1px solid #DFE7F3;
                border-bottom: 1px solid #DFE7F3;
                font-weight: 600;
            }
            """
        )
        if len(selected_keys) == 1:
            key = selected_keys[0]
            df = self.last_suitable_by_criterion.get(key, pd.DataFrame())[show_cols].reset_index(drop=True)
            table.setAlternatingRowColors(True)
            table.setStyleSheet(table_style)
            table.setColumnCount(len(show_cols))
            table.setRowCount(len(df))
            table.setHorizontalHeaderLabels([col_titles_ru.get(col, col) for col in show_cols])
            for r in range(len(df)):
                for c, col in enumerate(show_cols):
                    table.setItem(r, c, QTableWidgetItem(str(df.iloc[r, c])))
            table.resizeColumnsToContents()
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            layout.addWidget(table)
        else:
            tabs = QTabWidget()
            cfg_map = self.condition_configs()
            for key in selected_keys:
                df_src = self.last_suitable_by_criterion.get(key, pd.DataFrame())
                df = df_src[show_cols].reset_index(drop=True) if not df_src.empty else pd.DataFrame(columns=show_cols)
                page = QWidget()
                page_layout = QVBoxLayout(page)
                page_table = QTableWidget()
                page_table.setAlternatingRowColors(True)
                page_table.setStyleSheet(table_style)
                page_table.setColumnCount(len(show_cols))
                page_table.setRowCount(len(df))
                page_table.setHorizontalHeaderLabels([col_titles_ru.get(col, col) for col in show_cols])
                for r in range(len(df)):
                    for c, col in enumerate(show_cols):
                        page_table.setItem(r, c, QTableWidgetItem(str(df.iloc[r, c])))
                page_table.resizeColumnsToContents()
                page_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
                page_layout.addWidget(page_table)
                tabs.addTab(page, cfg_map[key]["title"])
            layout.addWidget(tabs)
        dlg.exec_()


def main():
    app = QApplication(sys.argv)
    window = AshbyDiagramWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
