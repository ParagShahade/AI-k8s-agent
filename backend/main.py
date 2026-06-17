from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.logging import setup_logging
from api.health import router as health_router
from api.investigate import router as investigate_router
from api.clusters import router as clusters_router

setup_logging()

app = FastAPI(
    title="AI Kubernetes Agent",
    description="On-demand Kubernetes troubleshooting with AI",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(investigate_router)
app.include_router(clusters_router)
