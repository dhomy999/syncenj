import os
import sys
from pathlib import Path

# Allow importing from project root (enjazi/, config/)
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.database import init_db
from backend.scheduler import scheduler, load_jobs_from_db, ensure_default_jobs
from backend.routers import jobs, data, logs, import_csv, student_page, halaqat, students
from enjazi.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    logger.info("Starting Enjazi Automation Backend...")
    init_db()
    logger.info("Database initialized.")
    scheduler.start()
    ensure_default_jobs()
    load_jobs_from_db()
    logger.info("Scheduler started.")
    yield
    # --- Shutdown ---
    scheduler.shutdown()
    logger.info("Scheduler stopped.")


app = FastAPI(
    title="Enjazi Automation API",
    description="نظام أتمتة إنجازي — إدارة المهام المجدولة",
    version="1.0.0",
    lifespan=lifespan,
)

_origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    # يسمح بأي منفذ محلي أو عنوان شبكة خاصة أثناء التطوير (localhost / 127.x / 192.168.x / 10.x / 172.16-31.x)
    allow_origin_regex=r"http://(localhost|127\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.(1[6-9]|2\d|3[01])\.\d+\.\d+)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router,  prefix="/api/jobs",  tags=["المهام"])
app.include_router(data.router,  prefix="/api/data",  tags=["البيانات"])
app.include_router(logs.router,       prefix="/api/logs",   tags=["السجلات"])
app.include_router(import_csv.router, prefix="/api/import", tags=["الاستيراد"])
app.include_router(student_page.router, prefix="/api/student-page", tags=["لوحة الطالب"])
app.include_router(halaqat.router,  prefix="/api/halaqat",  tags=["الحلقات"])
app.include_router(students.router, prefix="/api/students", tags=["الطلاب"])


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "service": "Enjazi Automation Backend"}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
