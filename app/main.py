from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.config import settings
import uvicorn
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.domain.exceptions.exceptions import DomainException
from app.api.routes import webhook, admin, auth, management, onboarding, payplus
from app.api.dependencies import limiter, get_db


def create_app() -> FastAPI:
    app = FastAPI(title=settings.PROJECT_NAME)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(webhook.router, prefix="/api/v1/webhooks")
    app.include_router(admin.router, prefix="/api/v1/admin")
    app.include_router(management.router, prefix="/api/v1")
    app.include_router(onboarding.router, prefix="/api/v1")
    app.include_router(payplus.router, prefix="/api/v1/webhooks")

    @app.get("/")
    async def read_root():
        return {"message": "Welcome to LyraSync.ai"}

    @app.get("/health")
    async def health_check(db: AsyncSession = Depends(get_db)):
        try:
            # Ping database
            await db.execute(text("SELECT 1"))
            return {"status": "healthy", "version": "1.0.0", "database": "connected"}
        except Exception as e:
            return JSONResponse(
                status_code=503, 
                content={"status": "unhealthy", "database": "disconnected", "detail": str(e)}
            )

    @app.exception_handler(DomainException)
    async def domain_exception_handler(request: Request, exc: DomainException):
        return JSONResponse(status_code=400, content={"message": exc.message})

    return app


if __name__ == "__main__":
    app = create_app()
    uvicorn.run(app, host="127.0.0.1", port=8000)
