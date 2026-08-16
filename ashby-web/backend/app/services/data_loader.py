from functools import lru_cache
from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "materials_for_project"
PALETTE = ["#8e7cc3", "#6aa84f", "#e69138", "#3d85c6", "#cc4125", "#45818e", "#a64d79", "#f1c232"]

@lru_cache(maxsize=1)
def load_default_data() -> pd.DataFrame:
    materials = pd.read_csv(DATA_DIR / "Dataset_for_Ashby.csv", encoding="utf-8-sig")
    groups = pd.read_csv(DATA_DIR / "Group_materials.csv", encoding="utf-8-sig")
    subgroups = pd.read_csv(DATA_DIR / "Subgroup_materials.csv", encoding="utf-8-sig")
    for frame in (materials, groups, subgroups):
        frame.columns = frame.columns.str.strip()
    df = materials.merge(subgroups, on="subgroup_id", how="left").merge(groups, on="group_id", how="left")
    color_map = {gid: PALETTE[i % len(PALETTE)] for i, gid in enumerate(sorted(df["group_id"].dropna().unique()))}
    df["color"] = df["group_id"].map(color_map).fillna("#64748b")
    numeric = ["Density_kg_m3", "Youngs_Modulus_GPa", "Strength_MPa", "Thermal_Conductivity_W_mK", "Cost_EUR_kg", "E_over_rho", "Strength_over_rho", "SqrtE_over_rho"]
    for col in numeric:
        if col in df:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

def all_materials() -> list[dict]:
    return load_default_data().replace({pd.NA: None}).to_dict("records")

def groups_with_colors() -> list[dict]:
    df = load_default_data()
    return df[["group_id", "group_name", "color"]].drop_duplicates().rename(columns={"group_id":"id", "group_name":"name"}).to_dict("records")
