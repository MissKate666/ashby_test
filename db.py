import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse

# Создаем фигуру
fig, ax = plt.subplots(figsize=(10, 8))

# Логарифмические оси
ax.set_xscale("log")
ax.set_yscale("log")

# Пределы осей
ax.set_xlim(0.001, 100)
ax.set_ylim(0.1, 10000)

# Подписи
ax.set_xlabel("TOUGHNESS (kJ/m²)", fontsize=12)
ax.set_ylabel("STRENGTH (MPa)", fontsize=12)
ax.set_title("Ashby Chart\nStrength vs Toughness", fontsize=18)

# Сетка
ax.grid(True, which="both", linestyle="--", linewidth=0.5, alpha=0.6)

# Функция добавления области
def add_material_region(x, y, width, height, angle, color, label):
    ellipse = Ellipse(
        (x, y),
        width,
        height,
        angle=angle,
        facecolor=color,
        edgecolor="black",
        alpha=0.5,
        linewidth=1.2,
    )
    ax.add_patch(ellipse)
    ax.text(x, y, label, ha="center", va="center", fontsize=10, weight="bold")

# Добавляем области (примерные координаты для визуального сходства)

add_material_region(0.02, 200, 0.05, 800, 10, "#f4c542", "Glasses")
add_material_region(0.2, 20, 0.6, 40, 25, "#2ca58d", "Wood")
add_material_region(1, 50, 3, 100, 10, "#ff6b6b", "Polymers")
add_material_region(5, 500, 8, 2000, -10, "#8e7cc3", "Metals & alloys")
add_material_region(20, 1000, 40, 3000, 0, "#b4a7d6", "Composites")
add_material_region(0.005, 5, 0.02, 8, 0, "#d9b38c", "Ceramics")

# Улучшение визуала
for spine in ax.spines.values():
    spine.set_linewidth(1.5)

plt.tight_layout()
plt.show()