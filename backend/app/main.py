import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import logger
from app.api.routes import router as api_router
from app.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.PROJECT_NAME} Platform [Mode: {settings.APP_MODE}] [Provider: {settings.AI_PROVIDER}]...")
    # Initialize / verify schema in development mode
    if settings.APP_MODE in ("development", "demo"):
        init_db()
    logger.info(f"{settings.PROJECT_NAME} Engine ready.")
    yield
    logger.info(f"Shutting down {settings.PROJECT_NAME} Engine...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Enterprise Multi-Modal AI Fraud & Voice Deepfake Detection Platform. Fuses Voice Authenticity, 1:1 Speaker Verification, Intent Classification, and Telephony Signal Intelligence into Explainable Risk Decisions.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Setup
origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_and_timing_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Store request_id in request state for downstream handlers
    request.state.request_id = request_id

    response = await call_next(request)
    
    duration = time.time() - start_time
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{duration:.4f}s"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), geolocation=()"
    
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    logger.error(
        f"Unhandled exception during {request.method} {request.url.path}: {exc}",
        exc_info=True,
        extra={"request_id": req_id, "endpoint": request.url.path}
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred during security analysis. The incident has been securely logged.",
            "request_id": req_id,
            "request_path": request.url.path
        }
    )


# Mount versioned API routes under /api/v1 and legacy compatibility under /api
app.include_router(api_router, prefix="/api/v1")
app.include_router(api_router, prefix="/api")


# Kubernetes & Cloud Readiness Probes
@app.get("/health/live", summary="Liveness Probe")
async def liveness():
    return {"status": "LIVE", "timestamp": time.time()}


@app.get("/health/ready", summary="Readiness Probe")
async def readiness():
    from app.db.database import engine
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "READY", "database": "CONNECTED", "timestamp": time.time()}
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "NOT_READY", "database": str(e)}
        )


@app.get("/", summary="Root Status")
async def root():
    return {
        "product": "SentinelVoice",
        "tagline": "Don't Just Detect a Fake Voice. Detect the Fraud.",
        "status": "online",
        "version": settings.VERSION,
        "mode": settings.APP_MODE,
        "docs": "/docs",
        "api_v1": "/api/v1"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
