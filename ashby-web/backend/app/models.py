from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class Condition(str, Enum):
    none = "none"
    stiffness = "stiffness"
    strength = "strength"
    bending = "bending"
    plate_stiffness = "plate_stiffness"
    beam_strength = "beam_strength"
    column_stiffness = "column_stiffness"


class Preference(str, Enum):
    high = "high"
    low = "low"


class AnalyzeRequest(BaseModel):
    condition: Condition = Condition.stiffness
    preference: Preference = Preference.high
    x_min: Optional[float] = Field(default=None, gt=0)
    x_max: Optional[float] = Field(default=None, gt=0)
    y_min: Optional[float] = Field(default=None, gt=0)
    y_max: Optional[float] = Field(default=None, gt=0)
    intercept: Optional[float] = None

    @model_validator(mode="after")
    def validate_ranges(self):
        if self.x_min is not None and self.x_max is not None and self.x_min > self.x_max:
            raise ValueError("x_min must be less than or equal to x_max")
        if self.y_min is not None and self.y_max is not None and self.y_min > self.y_max:
            raise ValueError("y_min must be less than or equal to y_max")
        return self


class MaterialPoint(BaseModel):
    x: float
    y: float
    name: str
    group: str
    subgroup: str
    is_suitable: bool
    color: str
    density: float
    youngs_modulus: float
    strength: float
    e_over_rho: float | None = None
    strength_over_rho: float | None = None
    sqrte_over_rho: float | None = None


class GroupShape(BaseModel):
    id: int
    name: str
    color: str
    polygon: list[list[float]]
    subgroup: str | None = None
    kind: str = "group"


class ConditionLine(BaseModel):
    x: list[float]
    y: list[float]
    intercept: float
    slope: float


class AnalyzeResponse(BaseModel):
    points: list[MaterialPoint]
    groups: list[GroupShape]
    condition_line: ConditionLine | None
    suitable_count: int
    total_count: int
    x_range: tuple[float, float]
    y_range: tuple[float, float]
