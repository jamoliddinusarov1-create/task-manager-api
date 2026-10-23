"""
Ushbu modul ma'lumotlar bazasi (PostgreSQL) bilan ulanishni ta'minlaydi.
NIMA UCHUN KERAK:
- SQLAlchemy 2.0 orqali ma'lumotlar bazasi ulanish dvigatelini (engine) yaratish;
- Har bir API so'rovi uchun xavfsiz ma'lumotlar bazasi sessiyasini (Session) ochish;
- Sessiya yakunlangach, ulanishni yopish (connection leak bo'lmasligi uchun).
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from app.config import settings

# Database Engine: Ma'lumotlar bazasi bilan aloqa o'rnatuvchi asosiy obyekt.
# pool_pre_ping=True: Uzilib qolgan ulanishlarni so'rov yuborishdan oldin avtomatik tekshirib, qayta tiklaydi.
engine = create_engine(
    settings.sync_database_url,
    pool_pre_ping=True,
    echo=False
)

# Sessiyalar fabrikasi: Har bir so'rov uchun yangi ma'lumotlar bazasi sessiyasini ishlab chiqaradi.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


class Base(DeclarativeBase):
    """
    SQLAlchemy 2.0 modellarining umumiy ota klassi (Declarative Base).
    Barcha modellar (User, Project, Task) shu klassdan meros oladi va jadvallarni ro'yxatga oladi.
    """
    pass


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI Dependency Injection funksiyasi.
    NIMA QILMOQDA:
    1. Har bir HTTP so'rovi kelganda yangi DB sessiyasini ochadi (`db = SessionLocal()`);
    2. Endpointga ushbu sessiyani taqdim etadi (`yield db`);
    3. So'rov bajarilib bo'lgach (yoki xatolik yuz berganda ham), sessiyani xavfsiz yopadi (`db.close()`).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
