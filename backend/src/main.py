import uvicorn
from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from starlette import status
from starlette.middleware.cors import CORSMiddleware
from src.config import settings
from src.dependencies.database import get_db
from src.dependencies.redis import get_redis_service
from src.exceptions import register_exception_handlers
from src.routers.analytics import router as analytics_router
from src.routers.auth import router as auth_router
from src.routers.budgets import router as budgets_router
from src.routers.categories import router as categories_router
from src.routers.transactions import router as transactions_router
from src.services.redis_service import RedisService

app = FastAPI(
    title="Finance Tracker API",
    description="REST API трекера фінансів: доходи, витрати, бюджети та аналітика",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Токен ходить у заголовку, cookie немає
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count"],
)

register_exception_handlers(app)

app.include_router(auth_router)
app.include_router(categories_router)
app.include_router(transactions_router)
app.include_router(budgets_router)
app.include_router(analytics_router)

@app.get("/", tags=["Health"], summary="Health check")
def root():
    return {"status": "ok", "message": "Finance Tracker API is running 🚀"}

@app.get("/health", tags=["Health"], summary="Чи доступні БД і Redis")
def health(
        db: Session = Depends(get_db),
        redis_service: RedisService = Depends(get_redis_service)
):
    checks = {}
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "unavailable"
    try:
        redis_service.ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "unavailable"

    healthy = all(value == "ok" for value in checks.values())
    return JSONResponse(
        status_code=status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"status": "ok" if healthy else "degraded", **checks},
    )

if __name__ == '__main__':
    uvicorn.run("src.main:app", reload=True, host="0.0.0.0", port=8000)
