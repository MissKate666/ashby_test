from io import BytesIO, StringIO

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.models import AnalyzeRequest
from app.routers.api import dataset
from app.services.diagram import analyze

router = APIRouter(prefix="/api/export", tags=["export"])
EXPORT_COLUMNS = ["material_name", "group_name", "subgroup_name", "Density_kg_m3", "Youngs_Modulus_GPa", "Strength_MPa", "E_over_rho", "Strength_over_rho", "SqrtE_over_rho"]


def suitable_frame(request: AnalyzeRequest, data):
    df, groups = data
    result = analyze(df, groups, request)
    names = {p.name for p in result.points if p.is_suitable}
    return df[df["material_name"].isin(names)][[c for c in EXPORT_COLUMNS if c in df.columns]]


@router.get("/csv")
def export_csv(condition: str = "stiffness", preference: str = "high", x_min: float | None = None, x_max: float | None = None, y_min: float | None = None, y_max: float | None = None, intercept: float | None = None, data=Depends(dataset)):
    req = AnalyzeRequest(condition=condition, preference=preference, x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max, intercept=intercept)
    buffer = StringIO(); suitable_frame(req, data).to_csv(buffer, index=False)
    return StreamingResponse(iter([buffer.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=ashby_materials.csv"})


@router.get("/excel")
def export_excel(condition: str = "stiffness", preference: str = "high", x_min: float | None = None, x_max: float | None = None, y_min: float | None = None, y_max: float | None = None, intercept: float | None = None, data=Depends(dataset)):
    req = AnalyzeRequest(condition=condition, preference=preference, x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max, intercept=intercept)
    buffer = BytesIO()
    with __import__("pandas").ExcelWriter(buffer, engine="openpyxl") as writer:
        suitable_frame(req, data).to_excel(writer, index=False, sheet_name="Materials")
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=ashby_materials.xlsx"})
