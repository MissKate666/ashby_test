from io import BytesIO, StringIO

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import ValidationError

from app.models import AnalyzeRequest, Condition, Preference
from app.routers.api import dataset
from app.services.diagram import compute_suitable_mask

router = APIRouter(prefix="/api/export", tags=["export"])
EXPORT_COLUMNS = ["material_name", "group_name", "subgroup_name", "Density_kg_m3", "Youngs_Modulus_GPa", "Strength_MPa", "E_over_rho", "Strength_over_rho", "SqrtE_over_rho"]


def build_request(**kwargs) -> AnalyzeRequest:
    # AnalyzeRequest's own Field/model validators (x_min>0, x_min<=x_max, etc.) only
    # produce FastAPI's automatic 422 response when they run during request parsing.
    # Here the model is constructed manually inside the handler body, so a bad
    # combination of query params would otherwise surface as an unhandled 500.
    try:
        return AnalyzeRequest(**kwargs)
    except ValidationError as exc:
        # exc.errors() can embed the raw exception object in "ctx" for custom
        # validators, which json.dumps can't serialize -- keep only the
        # JSON-safe fields.
        errors = [{"loc": e["loc"], "msg": e["msg"], "type": e["type"]} for e in exc.errors()]
        raise HTTPException(422, errors) from exc


def suitable_frame(request: AnalyzeRequest, data):
    df, _groups = data
    suitable = compute_suitable_mask(df, request)
    return df.loc[suitable, [c for c in EXPORT_COLUMNS if c in df.columns]]


@router.get("/csv")
def export_csv(
    condition: Condition = Condition.stiffness,
    preference: Preference = Preference.high,
    x_min: float | None = Query(default=None, gt=0),
    x_max: float | None = Query(default=None, gt=0),
    y_min: float | None = Query(default=None, gt=0),
    y_max: float | None = Query(default=None, gt=0),
    intercept: float | None = Query(default=None, ge=-50, le=50),
    data=Depends(dataset),
):
    req = build_request(condition=condition, preference=preference, x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max, intercept=intercept)
    buffer = StringIO(); suitable_frame(req, data).to_csv(buffer, index=False)
    # Prefix a UTF-8 BOM: without it, Excel guesses the file's encoding from the
    # system locale instead of UTF-8, garbling the Cyrillic group/subgroup names.
    content = "﻿" + buffer.getvalue()
    return StreamingResponse(iter([content]), media_type="text/csv; charset=utf-8", headers={"Content-Disposition": "attachment; filename=ashby_materials.csv"})


@router.get("/excel")
def export_excel(
    condition: Condition = Condition.stiffness,
    preference: Preference = Preference.high,
    x_min: float | None = Query(default=None, gt=0),
    x_max: float | None = Query(default=None, gt=0),
    y_min: float | None = Query(default=None, gt=0),
    y_max: float | None = Query(default=None, gt=0),
    intercept: float | None = Query(default=None, ge=-50, le=50),
    data=Depends(dataset),
):
    req = build_request(condition=condition, preference=preference, x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max, intercept=intercept)
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        suitable_frame(req, data).to_excel(writer, index=False, sheet_name="Materials")
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=ashby_materials.xlsx"})
