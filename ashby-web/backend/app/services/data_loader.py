import logging
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from .translator import translate_series_to_russian

logger = logging.getLogger(__name__)

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
    orphaned = materials.loc[~materials["material_id"].isin(merged["material_id"]), "material_name"]
    if len(orphaned):
        logger.warning(
            "Dropped %d material(s) with no matching subgroup/group and excluded them from the app: %s",
            len(orphaned), ", ".join(orphaned.tolist()),
        )
    for col in ["subgroup_name", "material_name"]:
        merged[col] = translate_series_to_russian(merged[col])
    # The source CSV's precomputed E_over_rho/Strength_over_rho/SqrtE_over_rho columns
    # are unreliable (SqrtE_over_rho in particular is off by up to ~3x for several
    # materials) -- recompute all three live from the raw density/modulus/strength
    # columns so the values shown in tooltips/exports are internally consistent.
    density = pd.to_numeric(merged["Density_kg_m3"], errors="coerce")
    modulus = pd.to_numeric(merged["Youngs_Modulus_GPa"], errors="coerce")
    strength = pd.to_numeric(merged["Strength_MPa"], errors="coerce")
    merged["E_over_rho"] = modulus / density
    merged["Strength_over_rho"] = strength / density
    merged["SqrtE_over_rho"] = np.sqrt(modulus) / density
    return merged.reset_index(drop=True), groups
