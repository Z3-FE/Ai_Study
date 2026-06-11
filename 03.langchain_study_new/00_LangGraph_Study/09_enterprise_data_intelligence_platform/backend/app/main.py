from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import bootstrap, conversations, corpus, runs, semantic_assets, semantic_drafts, vector
from .settings import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description="Business API for the enterprise data intelligence platform.",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(bootstrap.router, prefix=settings.api_prefix)
    app.include_router(conversations.router, prefix=settings.api_prefix)
    app.include_router(runs.router, prefix=settings.api_prefix)
    app.include_router(corpus.router, prefix=settings.api_prefix)
    app.include_router(semantic_assets.router, prefix=settings.api_prefix)
    app.include_router(semantic_drafts.router, prefix=settings.api_prefix)
    app.include_router(vector.router, prefix=settings.api_prefix)

    return app


app = create_app()
