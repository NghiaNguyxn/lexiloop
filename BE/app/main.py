import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database.databases import init_initial_data
from app.common.exception_handler import register_exception_handlers
from app.core.config import settings
from app.users import router as user_router
from app.auth import router as auth_router
from app.decks import router as deck_router
from app.decks import admin_router as deck_admin_router
from app.vocabularies import router as vocabulary_router
from app.vocabularies import admin_router as vocabulary_admin_router


# Cấu hình Logging chuẩn: Thời gian xảy ra - Tên Module - Cấp độ lỗi - Nội dung chi tiết
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):

    init_initial_data()
    logger.info("Initial SQL data initialized")

    yield

    logger.info("Shutting down system...")


app = FastAPI(
    title="Lexi Loop",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).parent.parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# Đăng ký tất cả exception handlers
register_exception_handlers(app)


@app.get("/")
async def root():
    return {"message": "Welcome to the Lexi Loop API!"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


app.include_router(user_router.router)
app.include_router(auth_router.router)
app.include_router(deck_router.router)
app.include_router(deck_admin_router.router)
app.include_router(vocabulary_router.router)
app.include_router(vocabulary_admin_router.router)
