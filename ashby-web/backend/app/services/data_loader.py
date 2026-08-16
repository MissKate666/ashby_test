from functools import lru_cache
from pathlib import Path

import pandas as pd

from .translator import translate_series_to_russian

GROUP_COLORS = ["#003F88", "#D90429", "#2B9348", "#FFBA08", "#111111", "#00B4D8", "#F72585", "#FB5607", "#70E000", "#8338EC"]
DATA_DIR = Path(__file__).resolve().parents[2] / "materials_for_project"


@lru_cache(maxsize=1)
def load_default_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    groups = pd.read_csv(DATA_DIR / "Group_materials.csv", encoding="utf-8-sig")
    subgroups = pd.read_csv(DATA_DIR / "Subgroup_materials.csv", encoding="utf-8-sig")
    materials = pd.read_csv(DATA_DIR / "Dataset_for_Ashby.csv", encoding="utf-8-sig")
    for frame in (groups, subgroups, materials):
        frame.columns = frame.columns.str.strip()
    for frame, col in [(groups, "group_id"), (subgroups, "subgroup_id"), (subgroups, "group_id"), (materials, "subgroup_id")]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce").astype("Int64")
    groups = groups.sort_values("group_id").reset_index(drop=True)
    groups["group_name"] = translate_series_to_russian(groups["group_name"])
    groups["color"] = [GROUP_COLORS[i % len(GROUP_COLORS)] for i in range(len(groups))]
    merged = materials.merge(subgroups, on="subgroup_id", how="inner", validate="many_to_one").merge(groups[["group_id", "group_name", "color"]], on="group_id", how="inner", validate="many_to_one")
    for col in ["subgroup_name", "material_name"]:
        merged[col] = translate_series_to_russian(merged[col])
    if merged[["group_id", "group_name"]].isna().any().any():
        raise ValueError("Some materials are not linked to a material group")
    return merged.reset_index(drop=True), groups
