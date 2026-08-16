from typing import Literal
from pydantic import BaseModel, Field

Criterion = Literal["E_over_rho", "Strength_over_rho", "SqrtE_over_rho"]
Mode = Literal["high", "low"]

class AnalyzeRequest(BaseModel):
    x_axis: str = "Density_kg_m3"
    y_axis: str = "Youngs_Modulus_GPa"
    criterion: Criterion = "E_over_rho"
    mode: Mode = "high"
    intercept: float | None = None
    slope: float | None = None
    x_min: float | None = Field(default=None, gt=0)
    x_max: float | None = Field(default=None, gt=0)
    y_min: float | None = Field(default=None, gt=0)
    y_max: float | None = Field(default=None, gt=0)

class MaterialPoint(BaseModel):
    x: float
    y: float
    name: str
    group: str
    subgroup: str
    is_suitable: bool
    color: str

class GroupShape(BaseModel):
    id: int
    name: str
    color: str
    polygon: list[list[float]]

class ConditionLine(BaseModel):
    x: list[float]
    y: list[float]
    intercept: float
    slope: float

class AnalyzeResponse(BaseModel):
    points: list[MaterialPoint]
    groups: list[GroupShape]
    condition_line: ConditionLine
    suitable_count: int
    total_count: int
    x_range: tuple[float, float]
    y_range: tuple[float, float]
