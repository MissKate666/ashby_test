from io import BytesIO, StringIO
import pandas as pd
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models import AnalyzeRequest
from app.services.data_loader import load_default_data
from app.services.diagram import analyze

router = APIRouter(prefix="/api/export", tags=["export"])

def suitable_frame(params: AnalyzeRequest) -> pd.DataFrame:
    df = load_default_data()
    result = analyze(df, params)
    names = {p["name"] for p in result["points"] if p["is_suitable"]}
    return df[df["material_name"].isin(names)]

@router.get("/csv")
def export_csv(params: AnalyzeRequest = AnalyzeRequest()):
    try:
        data = suitable_frame(params)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    buffer = StringIO(); data.to_csv(buffer, index=False)
    return StreamingResponse(iter([buffer.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=suitable_materials.csv"})

@router.get("/excel")
def export_excel(params: AnalyzeRequest = AnalyzeRequest()):
    try:
        data = suitable_frame(params)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        data.to_excel(writer, index=False, sheet_name="Suitable materials")
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=suitable_materials.xlsx"})
