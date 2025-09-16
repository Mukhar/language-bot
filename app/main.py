from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog
from datetime import datetime

from .config import get_settings
from .database import create_tables
from .routers import scenarios, responses
from .schemas import HealthResponse


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan management
    """
    # Startup
    logger.info("Starting Simple Healthcare Communication Bot API")
    
    try:
        logger.info("Creating/verifying database tables...")
        create_tables()
        logger.info("Database tables created/verified successfully")
    except Exception as e:
        logger.error("Failed to create/verify database tables", error=str(e), exc_info=True)
        # Don't fail startup - let the app start and handle DB errors per request
        logger.warning("Application starting without database verification")
    
    logger.info("Application startup completed")
    yield
    
    # Shutdown
    logger.info("Shutting down Simple Healthcare Communication Bot API")


# Initialize simplified FastAPI app
app = FastAPI(
    title="Simple Healthcare Communication Practice Bot",
    description="Simple AI-powered healthcare communication training platform",
    version="1.0.0",
    lifespan=lifespan
)

# Get settings
settings = get_settings()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include simplified routers
app.include_router(scenarios.router)
app.include_router(responses.router)


@app.get("/", response_model=HealthResponse)
async def root():
    """
    Root endpoint - health check
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0"
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0"
    )


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled errors
    """
    logger.error("Unhandled exception", 
                 path=request.url.path,
                 method=request.method,
                 error=str(exc),
                 exc_info=True)
    
    raise HTTPException(
        status_code=500,
        detail="An internal server error occurred. Please try again later."
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
