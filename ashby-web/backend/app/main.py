from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import api, export
from app.services.data_loader import load_default_data

app = FastAPI(title="Ashby Diagram Web API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(api.router)
app.include_router(export.router)

@app.on_event("startup")
def warm_cache() -> None:
    load_default_data()

@app.get("/health")
def health():
    return {"status": "ok", "materials": len(load_default_data())}
