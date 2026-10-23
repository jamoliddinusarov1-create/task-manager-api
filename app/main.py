"""
FastAPI ilovasining asosiy kirish nuqtasi (Entrypoint).
NIMA UCHUN KERAK:
- FastAPI ilovasini ishga tushirish, sarlavha va versiyasini belgilash;
- CORS xavfsizlik qoidalarini ulash;
- Swagger (/docs) va ReDoc (/redoc) interaktiv hujjatlarini ulash;
- EC2 deploy va monitoring uchun GET /health endpointini taqdim etish;
- Barcha v1 API yo'llarini (auth, users, projects, tasks) tizimga ulash.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.config import settings
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.projects import router as projects_router
from app.api.v1.tasks import router as tasks_router

# FastAPI asosiy ilovasini yaratish
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Task Manager API by Jamoliddin O'sarov - Imtihon Loyihasi #6",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS (Cross-Origin Resource Sharing) middleware:
# Frontend yoki boshqa domenlardan API ga xavfsiz so'rov yuborishga ruxsat berish
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
def root():
    """Bosh sahifaga (/) kirganda avtomatik ravishda Swagger (/docs) ga yo'naltirish."""
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["Health"], summary="Ilovaning sog'lomlik holatini tekshirish")
def health_check():
    """
    IMTIHON TALABI BO'YICHA:
    AWS EC2 deploy jarayonida va monitoringda ilova ishlab turganini tasdiqlash uchun endpoint.
    Deploy skripti ushbu endpointga curl so'rovini yuboradi.
    """
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }


# Barcha API v1 marshrutlarini (Routers) ulash
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(projects_router, prefix=settings.API_V1_STR)
app.include_router(tasks_router, prefix=settings.API_V1_STR)
