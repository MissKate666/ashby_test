from fastapi import APIRouter, Depends
import pandas as pd

from app.models import AnalyzeRequest, AnalyzeResponse
from app.services.data_loader import load_default_data
from app.services.diagram import analyze

router = APIRouter(prefix="/api", tags=["ashby"])


def dataset() -> tuple[pd.DataFrame, pd.DataFrame]:
    return load_default_data()


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_materials(request: AnalyzeRequest, data=Depends(dataset)):
    df, groups = data
    return analyze(df, groups, request)


@router.get("/materials")
def materials(data=Depends(dataset)):
    df, _ = data
    return df.replace({float("nan"): None}).to_dict(orient="records")


@router.get("/groups")
def groups(data=Depends(dataset)):
    _, groups_df = data
    return groups_df.to_dict(orient="records")
