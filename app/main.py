import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.schemas import HealthResponse
from app.core.config import settings
from app.utils.logger import setup_logger
from app.database import create_tables, test_connection
from app.routes.resume_routes import router as resume_router


setup_logger()
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""

    logger.info("Starting Resume Parser Application")
    await create_tables()
    logger.info("Database tables created/verified")

    yield

    logger.info("Shutting down Resume Parser Application")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Production-grade resume parsing application using FastAPI, LangChain, and OpenAI GPT-4",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.BACKEND_CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(resume_router, prefix=settings.API_V1_STR)

    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "message": "Resume Parser API",
            "version": settings.APP_VERSION,
            "docs": "/docs",
        }

    @app.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
    async def health_check():
        """Health check endpoint"""
        return HealthResponse(
            status=status.HTTP_200_OK,
            version=settings.APP_VERSION,
            database="connected" if await test_connection() else "Failed",
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc):
        logger.error(f"HTTP Exception: {exc.detail}")
        return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc):
        logger.error(f"Validation Error: {exc.errors()}")
        return JSONResponse(
            status_code=422,
            content={"error": "Validation error", "details": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc):
        logger.error(f"Unhandled Exception: {str(exc)}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": "Internal server error"})

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG
    )
