import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers import api, export
from app.services.data_loader import load_default_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Ashby Diagram API", version="1.0.0")
# No cookie/session-based auth exists in this API, so credentialed CORS requests
# serve no purpose here -- allow_credentials=True combined with a wildcard origin
# is a real spec violation (browsers reject it, or Starlette reflects the caller's
# Origin verbatim, defeating the point of restricting origins at all).
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])
app.include_router(api.router)
app.include_router(export.router)


@app.on_event("startup")
def warm_cache():
    load_default_data()


@app.exception_handler(Exception)
async def log_unhandled_exceptions(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health")
def health():
    return {"status": "ok"}
