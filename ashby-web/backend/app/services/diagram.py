import math
import numpy as np
import pandas as pd
try:
    from shapely.geometry import MultiPoint
    from shapely.ops import unary_union
except ModuleNotFoundError:  # graceful fallback for minimal environments; production requirements include shapely
    MultiPoint = None
    unary_union = None
from app.models import AnalyzeRequest

DEFAULT_SLOPES = {"E_over_rho": 1.0, "Strength_over_rho": 1.0, "SqrtE_over_rho": 0.5}


def current_condition_config(req: AnalyzeRequest, x_values: pd.Series, y_values: pd.Series) -> tuple[float, float]:
    slope = req.slope if req.slope is not None else DEFAULT_SLOPES[req.criterion]
    lx = np.log10(x_values.astype(float))
    ly = np.log10(y_values.astype(float))
    scores = ly - slope * lx
    default_intercept = float(np.nanpercentile(scores, 65 if req.mode == "high" else 35))
    return float(req.intercept if req.intercept is not None else default_intercept), float(slope)


def build_mask(df: pd.DataFrame, req: AnalyzeRequest) -> pd.Series:
    if req.x_axis not in df.columns or req.y_axis not in df.columns:
        raise ValueError("Выбранные оси отсутствуют в наборе данных")
    x = pd.to_numeric(df[req.x_axis], errors="coerce")
    y = pd.to_numeric(df[req.y_axis], errors="coerce")
    mask = x.notna() & y.notna() & (x > 0) & (y > 0)
    if req.x_min is not None: mask &= x >= req.x_min
    if req.x_max is not None: mask &= x <= req.x_max
    if req.y_min is not None: mask &= y >= req.y_min
    if req.y_max is not None: mask &= y <= req.y_max
    return mask


def rounded_geometry_from_log_points(points: list[tuple[float, float]]):
    if len(points) < 3:
        return None
    log_points = [(math.log10(x), math.log10(y)) for x, y in points if x > 0 and y > 0]
    if len(log_points) < 3:
        return None
    if MultiPoint is None:
        ordered = sorted(log_points)
        return [[10 ** x, 10 ** y] for x, y in ordered]
    geom = MultiPoint(log_points).convex_hull.buffer(0.08, join_style=1).buffer(-0.025, join_style=1)
    return geom if not geom.is_empty else None


def rounded_patch_from_log_points(points: list[tuple[float, float]]) -> list[list[float]]:
    geom = rounded_geometry_from_log_points(points)
    if geom is None:
        return []
    if isinstance(geom, list):
        return geom
    if geom.geom_type != "Polygon":
        geom = unary_union(geom).convex_hull
    coords = list(geom.exterior.coords)
    return [[10 ** x, 10 ** y] for x, y in coords]


def analyze(df: pd.DataFrame, req: AnalyzeRequest) -> dict:
    mask = build_mask(df, req)
    filtered = df.loc[mask].copy()
    if filtered.empty:
        raise ValueError("Нет данных после фильтрации")
    x = pd.to_numeric(filtered[req.x_axis], errors="coerce")
    y = pd.to_numeric(filtered[req.y_axis], errors="coerce")
    intercept, slope = current_condition_config(req, x, y)
    boundary = intercept + slope * np.log10(x)
    suitable = (np.log10(y) >= boundary) if req.mode == "high" else (np.log10(y) <= boundary)
    points = []
    for (_, row), ok, xv, yv in zip(filtered.iterrows(), suitable, x, y):
        points.append({"x": float(xv), "y": float(yv), "name": str(row.get("material_name", "")), "group": str(row.get("group_name", "")), "subgroup": str(row.get("subgroup_name", "")), "is_suitable": bool(ok), "color": str(row.get("color", "#64748b"))})
    groups = []
    for gid, gdf in filtered.groupby("group_id", dropna=True):
        pairs = list(zip(pd.to_numeric(gdf[req.x_axis], errors="coerce"), pd.to_numeric(gdf[req.y_axis], errors="coerce")))
        groups.append({"id": int(gid), "name": str(gdf["group_name"].iloc[0]), "color": str(gdf["color"].iloc[0]), "polygon": rounded_patch_from_log_points(pairs)})
    x_min, x_max, y_min, y_max = map(float, (x.min(), x.max(), y.min(), y.max()))
    line_x = np.logspace(np.log10(x_min), np.log10(x_max), 80)
    line_y = 10 ** (intercept + slope * np.log10(line_x))
    return {"points": points, "groups": groups, "condition_line": {"x": line_x.tolist(), "y": line_y.tolist(), "intercept": intercept, "slope": slope}, "suitable_count": int(suitable.sum()), "total_count": len(points), "x_range": (x_min, x_max), "y_range": (y_min, y_max)}
