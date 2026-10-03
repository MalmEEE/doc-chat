from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.services.embeddings import get_model
from app.api import documents
from app.errors import AppError, app_error_handler

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_model()   # warm up, so the first upload isn't slow
    yield


app = FastAPI(title="DocChat API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_exception_handler(AppError, app_error_handler)
app.include_router(documents.router)

@app.get("/api/health")
def health():
    return {"status": "ok"}