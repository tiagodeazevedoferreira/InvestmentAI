from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import router
from .api.paper_routes import router as paper_router
from .settings import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0", description="Investment research, simulation, ML and controlled execution platform")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["*"])
app.include_router(router, prefix="/api")
app.include_router(paper_router, prefix="/api")

@app.get("/")
def root():
    return {"application": settings.app_name, "docs": "/docs", "mode": settings.trading_mode.value}
