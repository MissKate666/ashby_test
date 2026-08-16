from fastapi import APIRouter, HTTPException
from app.models import AnalyzeRequest, AnalyzeResponse
from app.services.data_loader import all_materials, groups_with_colors, load_default_data
from app.services.diagram import analyze

router = APIRouter(prefix="/api", tags=["api"])

@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_materials(request: AnalyzeRequest):
    try:
        return analyze(load_default_data(), request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@router.get("/materials")
def materials():
    return all_materials()

@router.get("/groups")
def groups():
    return groups_with_colors()
