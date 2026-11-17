from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.config import get_settings
from app.database import SessionLocal
from app.routers import assistant, auth, budgets, categories, dashboard, expenses, exports, model, users
from app.services.categories import ensure_default_categories


@asynccontextmanager
async def lifespan(_app: FastAPI):
    with SessionLocal() as db:
        ensure_default_categories(db)
    yield


app = FastAPI(
    title="Mes Dépenses",
    description="API commune au site web, à l'application mobile et à l'application desktop.",
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

api = APIRouter(prefix="/api/v1")
for module in (auth, users, categories, expenses, budgets, dashboard, exports, model, assistant):
    api.include_router(module.router)
app.include_router(api)


@app.get("/health", tags=["Supervision"])
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}
