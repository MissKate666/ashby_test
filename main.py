import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QComboBox, QPushButton, QLabel,
                             QFileDialog, QMessageBox, QGroupBox, QGridLayout,
                             QCheckBox)
from PyQt5.QtCore import Qt


class AshbyDiagramWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.df = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Ashby Diagram Generator - Materials Project')
        self.setGeometry(100, 100, 1300, 900)

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Основной layout
        main_layout = QHBoxLayout(central_widget)

        # Левая панель с настройками
        control_panel = QWidget()
        control_panel.setMaximumWidth(350)
        control_layout = QVBoxLayout(control_panel)

        # Группа загрузки файла
        file_group = QGroupBox("File Selection")
        file_layout = QVBoxLayout()

        self.load_btn = QPushButton('Load CSV File (mp_all.csv)')
        self.load_btn.clicked.connect(self.load_csv)
        file_layout.addWidget(self.load_btn)

        self.file_label = QLabel('No file loaded')
        self.file_label.setWordWrap(True)
        file_layout.addWidget(self.file_label)

        file_group.setLayout(file_layout)
        control_layout.addWidget(file_group)

        # Группа фильтрации данных
        filter_group = QGroupBox("Data Filtering")
        filter_layout = QVBoxLayout()

        self.filter_stable = QCheckBox('Show only stable materials (e_above_hull = 0)')
        self.filter_stable.setChecked(True)
        filter_layout.addWidget(self.filter_stable)

        self.filter_metals = QCheckBox('Show only metals (band_gap = 0)')
        filter_layout.addWidget(self.filter_metals)

        self.filter_insulators = QCheckBox('Show only insulators (band_gap > 0)')
        filter_layout.addWidget(self.filter_insulators)

        filter_group.setLayout(filter_layout)
        control_layout.addWidget(filter_group)

        # Группа выбора осей
        axes_group = QGroupBox("Axis Selection")
        axes_layout = QGridLayout()

        axes_layout.addWidget(QLabel('X Axis:'), 0, 0)
        self.x_combo = QComboBox()
        axes_layout.addWidget(self.x_combo, 0, 1)

        axes_layout.addWidget(QLabel('Y Axis:'), 1, 0)
        self.y_combo = QComboBox()
        axes_layout.addWidget(self.y_combo, 1, 1)

        axes_group.setLayout(axes_layout)
        control_layout.addWidget(axes_group)

        # Группа настроек отображения
        display_group = QGroupBox("Plot Settings")
        display_layout = QVBoxLayout()

        self.log_x = QCheckBox('Logarithmic X axis')
        self.log_x.setChecked(True)
        display_layout.addWidget(self.log_x)

        self.log_y = QCheckBox('Logarithmic Y axis')
        self.log_y.setChecked(True)
        display_layout.addWidget(self.log_y)

        self.show_ashby = QCheckBox('Show Ashby regions (for K_VRH vs G_VRH)')
        self.show_ashby.setChecked(True)
        display_layout.addWidget(self.show_ashby)

        self.show_indices = QCheckBox('Show performance indices')
        self.show_indices.setChecked(True)
        display_layout.addWidget(self.show_indices)

        self.color_by_bandgap = QCheckBox('Color by band gap')
        self.color_by_bandgap.setChecked(True)
        display_layout.addWidget(self.color_by_bandgap)

        display_group.setLayout(display_layout)
        control_layout.addWidget(display_group)

        # Кнопка обновления
        self.update_btn = QPushButton('Update Plot')
        self.update_btn.clicked.connect(self.update_plot)
        self.update_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 8px; }")
        control_layout.addWidget(self.update_btn)

        # Информация о данных
        info_group = QGroupBox("Data Info")
        info_layout = QVBoxLayout()

        self.data_info_label = QLabel('No data loaded')
        self.data_info_label.setWordWrap(True)
        info_layout.addWidget(self.data_info_label)

        info_group.setLayout(info_layout)
        control_layout.addWidget(info_group)

        control_layout.addStretch()

        # Правая панель с графиком
        plot_panel = QWidget()
        plot_layout = QVBoxLayout(plot_panel)

        # Создаем фигуру matplotlib
        self.figure = plt.figure(figsize=(12, 9))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        plot_layout.addWidget(self.toolbar)
        plot_layout.addWidget(self.canvas)

        # Добавляем панели в основной layout
        main_layout.addWidget(control_panel)
        main_layout.addWidget(plot_panel, stretch=1)

        # Предопределенные области для диаграммы Эшби
        self.ashby_regions = {
            "Metals": {
                "K_range": (50e9, 250e9),  # GPa
                "G_range": (20e9, 150e9),  # GPa
                "color": "#8e7cc3",
                "alpha": 0.3
            },
            "Polymers": {
                "K_range": (1e9, 5e9),
                "G_range": (0.1e9, 2e9),
                "color": "#ff6b6b",
                "alpha": 0.3
            },
            "Ceramics": {
                "K_range": (100e9, 400e9),
                "G_range": (50e9, 200e9),
                "color": "#f4c542",
                "alpha": 0.3
            }
        }

    def load_csv(self):
        """Загрузка CSV файла"""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open CSV File",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )

        if file_name:
            try:
                # Пробуем разные кодировки
                encodings = ['utf-8', 'cp1251', 'latin1', 'iso-8859-1']
                self.df = None

                for encoding in encodings:
                    try:
                        self.df = pd.read_csv(file_name, encoding=encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                    except Exception as e:
                        print(f"Error with encoding {encoding}: {e}")
                        continue

                if self.df is None:
                    # Последняя попытка с автоопределением
                    self.df = pd.read_csv(file_name, encoding=None)

                self.file_label.setText(f'Loaded: {file_name.split("/")[-1]}')

                # Очищаем названия колонок от лишних пробелов
                self.df.columns = self.df.columns.str.strip()

                # Конвертируем все возможные колонки в числовой формат
                for col in self.df.columns:
                    try:
                        self.df[col] = pd.to_numeric(self.df[col], errors='ignore')
                    except:
                        pass

                # Обновляем комбобоксы
                self.update_column_combo()

                # Показываем информацию о данных
                self.update_data_info()

                # Автоматически строим график
                self.update_plot()

                QMessageBox.information(self, "Success",
                                        f"File loaded successfully!\n"
                                        f"Rows: {len(self.df)}\n"
                                        f"Columns: {len(self.df.columns)}")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load file:\n{str(e)}")

    def update_column_combo(self):
        """Обновление списков колонок"""
        if self.df is not None:
            # Получаем только числовые колонки
            numeric_columns = []
            for col in self.df.columns:
                try:
                    # Проверяем, можно ли конвертировать в числа
                    pd.to_numeric(self.df[col].iloc[0] if len(self.df) > 0 else 0)
                    numeric_columns.append(col)
                except:
                    # Если не получается, пропускаем
                    pass

            # Если не нашли числовых колонок, показываем все
            if not numeric_columns:
                numeric_columns = list(self.df.columns)

            self.x_combo.clear()
            self.y_combo.clear()
            self.x_combo.addItems(numeric_columns)
            self.y_combo.addItems(numeric_columns)

            # Устанавливаем разумные значения по умолчанию
            preferred_x = ['elasticity.K_VRH', 'K_VRH', 'bulk_modulus', 'volume', 'density']
            preferred_y = ['elasticity.G_VRH', 'G_VRH', 'shear_modulus', 'band_gap', 'energy_per_atom']

            for pref in preferred_x:
                if pref in numeric_columns:
                    self.x_combo.setCurrentText(pref)
                    break

            for pref in preferred_y:
                if pref in numeric_columns:
                    self.y_combo.setCurrentText(pref)
                    break

    def update_data_info(self):
        """Обновление информации о данных"""
        if self.df is not None:
            info_text = f"Total materials: {len(self.df)}\n"
            info_text += f"Total columns: {len(self.df.columns)}\n"

            # Статистика по стабильности
            if 'e_above_hull' in self.df.columns:
                try:
                    e_above = pd.to_numeric(self.df['e_above_hull'], errors='coerce')
                    stable = (e_above == 0).sum()
                    info_text += f"Stable materials (e_above_hull=0): {stable}\n"
                except:
                    pass

            # Статистика по band_gap
            if 'band_gap' in self.df.columns:
                try:
                    band_gap = pd.to_numeric(self.df['band_gap'], errors='coerce')
                    metals = (band_gap == 0).sum()
                    insulators = (band_gap > 0).sum()
                    info_text += f"Metals (band_gap=0): {metals}\n"
                    info_text += f"Insulators (band_gap>0): {insulators}\n"
                except:
                    pass

            self.data_info_label.setText(info_text)

    def filter_data(self):
        """Фильтрация данных по выбранным критериям"""
        if self.df is None:
            return None

        filtered_df = self.df.copy()

        # Фильтр по стабильности
        if self.filter_stable.isChecked() and 'e_above_hull' in filtered_df.columns:
            try:
                e_above = pd.to_numeric(filtered_df['e_above_hull'], errors='coerce')
                filtered_df = filtered_df[e_above == 0]
            except:
                pass

        # Фильтр по металлам
        if self.filter_metals.isChecked() and 'band_gap' in filtered_df.columns:
            try:
                band_gap = pd.to_numeric(filtered_df['band_gap'], errors='coerce')
                filtered_df = filtered_df[band_gap == 0]
            except:
                pass

        # Фильтр по изоляторам
        if self.filter_insulators.isChecked() and 'band_gap' in filtered_df.columns:
            try:
                band_gap = pd.to_numeric(filtered_df['band_gap'], errors='coerce')
                filtered_df = filtered_df[band_gap > 0]
            except:
                pass

        return filtered_df

    def add_ashby_regions(self, ax):
        """Добавление областей Эшби для модулей упругости"""
        # Конвертируем в GPa для удобства отображения
        for material_class, props in self.ashby_regions.items():
            K_min, K_max = props["K_range"]
            G_min, G_max = props["G_range"]

            # Создаем прямоугольную область
            rect = plt.Rectangle(
                (K_min, G_min),
                K_max - K_min,
                G_max - G_min,
                facecolor=props["color"],
                edgecolor="black",
                alpha=props["alpha"],
                linewidth=1.5,
                label=material_class
            )
            ax.add_patch(rect)

            # Добавляем текст
            ax.text(
                (K_min + K_max) / 2,
                (G_min + G_max) / 2,
                material_class,
                ha="center",
                va="center",
                fontsize=10,
                weight="bold",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.7)
            )

    def update_plot(self):
        """Обновление графика"""
        if self.df is None:
            QMessageBox.warning(self, "Warning", "Please load a CSV file first.")
            return

        x_col = self.x_combo.currentText()
        y_col = self.y_combo.currentText()

        if not x_col or not y_col:
            QMessageBox.warning(self, "Warning", "Please select both X and Y axes.")
            return

        try:
            # Применяем фильтры
            filtered_df = self.filter_data()

            if filtered_df is None or len(filtered_df) == 0:
                QMessageBox.warning(self, "Warning", "No data after filtering.")
                return

            # Получаем данные
            x_data = pd.to_numeric(filtered_df[x_col], errors='coerce')
            y_data = pd.to_numeric(filtered_df[y_col], errors='coerce')

            # Удаляем NaN значения
            mask = ~(x_data.isna() | y_data.isna())

            # Для логарифмического масштаба нужны положительные значения
            if self.log_x.isChecked():
                mask &= (x_data > 0)
            if self.log_y.isChecked():
                mask &= (y_data > 0)

            x_clean = x_data[mask]
            y_clean = y_data[mask]

            if len(x_clean) == 0:
                QMessageBox.warning(self, "Warning",
                                    "No valid data points after filtering.\n"
                                    "Try:\n"
                                    "1. Disabling logarithmic scale\n"
                                    "2. Changing filters\n"
                                    "3. Selecting different columns")
                return

            # Очищаем фигуру
            self.figure.clear()
            ax = self.figure.add_subplot(111)

            # Настройка масштаба осей
            if self.log_x.isChecked() and x_clean.min() > 0:
                ax.set_xscale("log")
            if self.log_y.isChecked() and y_clean.min() > 0:
                ax.set_yscale("log")

            # Добавляем данные
            if self.color_by_bandgap.isChecked() and 'band_gap' in filtered_df.columns:
                # Раскрашиваем по band_gap
                band_gap = pd.to_numeric(filtered_df.loc[mask, 'band_gap'], errors='coerce')
                if not band_gap.isna().all():
                    scatter = ax.scatter(x_clean, y_clean,
                                         c=band_gap, cmap='viridis',
                                         alpha=0.6, s=30, edgecolors='black',
                                         linewidth=0.5, zorder=3)
                    plt.colorbar(scatter, ax=ax, label='Band Gap (eV)')
                else:
                    ax.scatter(x_clean, y_clean,
                               alpha=0.6, s=30, c='blue',
                               edgecolors='black', linewidth=0.5, zorder=3)
            else:
                ax.scatter(x_clean, y_clean,
                           alpha=0.6, s=30, c='blue',
                           edgecolors='black', linewidth=0.5, zorder=3)

            # Добавляем области Эшби для модулей упругости
            if self.show_ashby.isChecked():
                if ('K_VRH' in x_col or 'bulk' in x_col.lower()) and ('G_VRH' in y_col or 'shear' in y_col.lower()):
                    self.add_ashby_regions(ax)

            # Настройка подписей
            x_label = x_col
            y_label = y_col

            # Добавляем единицы измерения
            units = {
                'elasticity.K_VRH': 'Bulk Modulus (GPa)',
                'K_VRH': 'Bulk Modulus (GPa)',
                'elasticity.G_VRH': 'Shear Modulus (GPa)',
                'G_VRH': 'Shear Modulus (GPa)',
                'band_gap': 'Band Gap (eV)',
                'energy_per_atom': 'Energy per Atom (eV/atom)',
                'formation_energy_per_atom': 'Formation Energy (eV/atom)',
                'total_magnetization': 'Total Magnetization (μB)',
                'e_above_hull': 'Energy Above Hull (eV/atom)'
            }

            if x_col in units:
                x_label = units[x_col]
            if y_col in units:
                y_label = units[y_col]

            ax.set_xlabel(x_label, fontsize=12)
            ax.set_ylabel(y_label, fontsize=12)

            # Заголовок
            title = f'Materials Properties: {y_col} vs {x_col}'
            if len(filtered_df) < len(self.df):
                title += f'\n(Showing {len(x_clean)} of {len(self.df)} materials)'
            ax.set_title(title, fontsize=14, fontweight='bold')

            # Сетка
            ax.grid(True, which="both", linestyle="--", alpha=0.3, zorder=0)

            # Настройка внешнего вида
            for spine in ax.spines.values():
                spine.set_linewidth(1.5)

            self.figure.tight_layout()
            self.canvas.draw()

            # Обновляем информацию
            stats_text = f"Displaying: {len(x_clean)} points\n"
            stats_text += f"X range: {x_clean.min():.2e} - {x_clean.max():.2e}\n"
            stats_text += f"Y range: {y_clean.min():.2e} - {y_clean.max():.2e}"
            self.data_info_label.setText(stats_text)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update plot:\n{str(e)}")
            import traceback
            traceback.print_exc()


def main():
    app = QApplication(sys.argv)
    window = AshbyDiagramWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()