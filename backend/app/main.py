from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import router
from .api.paper_routes import router as paper_router
from .settings import get_settings

settings = get_settings()


def _cors_origins(value: str) -> list[str]:
    origins = [item.strip() for item in value.split(",") if item.strip()]
    return origins or ["*"]


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Investment research, simulation, ML and controlled execution platform",
    docs_url="/docs" if settings.api_docs_enabled else None,
    redoc_url="/redoc" if settings.api_docs_enabled else None,
    openapi_url="/openapi.json" if settings.api_docs_enabled else None,
)
app.add_middleware(CORSMiddleware, allow_origins=_cors_origins(settings.cors_allowed_origins), allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["*"])


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    return response
app.include_router(router, prefix="/api")
app.include_router(paper_router, prefix="/api")

@app.get("/")
def root():
    return {"application": settings.app_name, "docs": "/docs", "mode": settings.trading_mode.value}
