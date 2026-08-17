import numpy as np
import pandas as pd
try:
    from shapely.geometry import LineString, MultiPoint, Point, Polygon
except ModuleNotFoundError:  # Allows lightweight validation when optional deps are unavailable.
    LineString = MultiPoint = Point = Polygon = None

from app.models import AnalyzeRequest, AnalyzeResponse, Condition, ConditionLine, GroupShape, MaterialPoint, Preference


def current_condition_config(condition: Condition):
    if condition == Condition.stiffness:
        return {"y_col": "Youngs_Modulus_GPa", "m": 1.0, "label": "E/ρ", "ratio_col": "E_over_rho", "to_b": lambda v: np.log10(v)}
    if condition == Condition.strength:
        return {"y_col": "Strength_MPa", "m": 1.0, "label": "σ/ρ", "ratio_col": "Strength_over_rho", "to_b": lambda v: np.log10(v)}
    if condition == Condition.bending:
        return {"y_col": "Youngs_Modulus_GPa", "m": 2.0, "label": "√E/ρ", "ratio_col": "SqrtE_over_rho", "to_b": lambda v: 2 * np.log10(v)}
    return None


def _fallback_polygon(points_log, padding=0.04):
    pts = np.asarray(points_log, dtype=float)
    if len(pts) == 0:
        return []
    if len(pts) == 1:
        a = np.linspace(0, 2 * np.pi, 24)
        pts = np.column_stack((pts[0,0] + padding * np.cos(a), pts[0,1] + padding * np.sin(a)))
    else:
        center = pts.mean(axis=0)
        pts = pts[np.argsort(np.arctan2(pts[:,1] - center[1], pts[:,0] - center[0]))]
    return np.column_stack((10 ** pts[:, 0], 10 ** pts[:, 1])).round(8).tolist()

def rounded_geometry_from_log_points(points_log, padding=0.0):
    if len(points_log) == 0:
        return None
    if Polygon is None:
        return _fallback_polygon(points_log, padding or 0.04)
    smooth_radius = 0.02
    if len(points_log) == 1:
        rounded = Point(points_log[0]).buffer(0.055 + padding, join_style=1)
    elif len(points_log) == 2:
        geom = LineString(points_log)
        seg = np.linalg.norm(np.array(points_log[0]) - np.array(points_log[1]))
        rounded = geom.buffer(max(seg * 0.24, 0.045) + padding, cap_style=1, join_style=1)
    else:
        hull = MultiPoint(points_log).convex_hull
        if not isinstance(hull, Polygon):
            return None
        minx, miny, maxx, maxy = hull.bounds
        radius = max(max(maxx - minx, maxy - miny) * 0.2, 0.035)
        rounded = hull.buffer(radius + padding, join_style=1).buffer(-radius, join_style=1)
        smooth_radius = radius * 0.35
    if rounded.is_empty:
        return None
    rounded = rounded.buffer(smooth_radius, join_style=1).buffer(-smooth_radius, join_style=1)
    if rounded.is_empty:
        return None
    return max(rounded.geoms, key=lambda g: g.area) if rounded.geom_type == "MultiPolygon" else rounded


def geometry_to_polygon(geom):
    if isinstance(geom, list):
        return geom
    if geom is None or geom.is_empty:
        return []
    if geom.geom_type == "MultiPolygon":
        geom = max(geom.geoms, key=lambda g: g.area)
    if geom.geom_type != "Polygon":
        return []
    coords = np.array(geom.exterior.coords)
    return np.column_stack((10 ** coords[:, 0], 10 ** coords[:, 1])).round(8).tolist()


def build_mask(df: pd.DataFrame, request: AnalyzeRequest, x_col: str, y_col: str, intercept: float):
    x = pd.to_numeric(df[x_col], errors="coerce")
    y = pd.to_numeric(df[y_col], errors="coerce")
    valid = (x > 0) & (y > 0) & np.isfinite(x) & np.isfinite(y)
    lx = np.log10(x[valid]); ly = np.log10(y[valid])
    cfg = current_condition_config(request.condition)
    if cfg:
        line_vals = cfg["m"] * lx + intercept
        cond = ly >= line_vals if request.preference == Preference.high else ly <= line_vals
    else:
        cond = pd.Series(True, index=lx.index)
    final = pd.Series(False, index=df.index)
    final.loc[valid.index[valid]] = cond.values
    if request.x_min is not None: final &= x >= request.x_min
    if request.x_max is not None: final &= x <= request.x_max
    if request.y_min is not None: final &= y >= request.y_min
    if request.y_max is not None: final &= y <= request.y_min if False else y <= request.y_max
    return x, y, final, valid


def analyze(df: pd.DataFrame, groups_df: pd.DataFrame, request: AnalyzeRequest) -> AnalyzeResponse:
    x_col = "Density_kg_m3"
    cfg = current_condition_config(request.condition)
    y_col = cfg["y_col"] if cfg else "Youngs_Modulus_GPa"
    base_valid = (pd.to_numeric(df[x_col], errors="coerce") > 0) & (pd.to_numeric(df[y_col], errors="coerce") > 0)
    intercept = request.intercept
    if cfg and intercept is None:
        ratios = pd.to_numeric(df.loc[base_valid, cfg["ratio_col"]], errors="coerce")
        ratios = ratios[(ratios > 0) & np.isfinite(ratios)]
        intercept = float(cfg["to_b"](float(ratios.median()))) if len(ratios) else 0.0
    intercept = float(intercept or 0.0)
    x, y, suitable, valid = build_mask(df, request, x_col, y_col, intercept)
    valid_df = df[valid].copy()
    x_vals = x[valid]; y_vals = y[valid]
    x_margin = y_margin = 10 ** 0.16
    x_range = (float(x_vals.min() / x_margin), float(x_vals.max() * x_margin))
    y_range = (float(y_vals.min() / y_margin), float(y_vals.max() * y_margin))
    shapes = []
    for row in groups_df.itertuples(index=False):
        gdf = valid_df[valid_df.group_id == row.group_id]
        poly = geometry_to_polygon(rounded_geometry_from_log_points(np.column_stack((np.log10(gdf[x_col]), np.log10(gdf[y_col]))) if len(gdf) else [], padding=0.028))
        shapes.append(GroupShape(id=int(row.group_id), name=row.group_name, color=row.color, polygon=poly))
        for subgroup, sdf in gdf.groupby("subgroup_name"):
            spoly = geometry_to_polygon(rounded_geometry_from_log_points(np.column_stack((np.log10(sdf[x_col]), np.log10(sdf[y_col]))), padding=0.01))
            if spoly:
                shapes.append(GroupShape(id=int(row.group_id), name=row.group_name, color=row.color, polygon=spoly, subgroup=str(subgroup), kind="subgroup"))
    points = [MaterialPoint(x=float(x.loc[i]), y=float(y.loc[i]), name=str(r.material_name), group=str(r.group_name), subgroup=str(r.subgroup_name), is_suitable=bool(suitable.loc[i]), color=str(r.color), density=float(r.Density_kg_m3), youngs_modulus=float(r.Youngs_Modulus_GPa), strength=float(r.Strength_MPa), e_over_rho=float(r.E_over_rho), strength_over_rho=float(r.Strength_over_rho), sqrte_over_rho=float(r.SqrtE_over_rho)) for i, r in valid_df.iterrows()]
    line = None
    if cfg:
        xs = np.logspace(np.log10(x_range[0]), np.log10(x_range[1]), 80)
        ys = 10 ** (cfg["m"] * np.log10(xs) + intercept)
        line = ConditionLine(x=xs.tolist(), y=ys.tolist(), intercept=intercept, slope=float(cfg["m"]))
    return AnalyzeResponse(points=points, groups=shapes, condition_line=line, suitable_count=int(suitable.sum()), total_count=int(valid.sum()), x_range=x_range, y_range=y_range)
