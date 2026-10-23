"""
Ushbu modul ilovaning barcha asosiy konfiguratsiyalarini boshqaradi.
NIMA UCHUN KERAK:
- Maxfiy ma'lumotlarni (SECRET_KEY, DB parollari) kod ichida ochiq qoldirmaslik;
- .env faylidagi parametrlarni xavfsiz o'qib, turini (str, int) validatsiya qilish;
- Pydantic Settings orqali loyihaning turli qismlarida yagona sozlamalar obyekti (settings) sifatida foydalanish.
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Ilovaning muhit o'zgaruvchilari (Environment Variables) klassi.
    .env faylida ko'rsatilgan qiymatlarni o'zlashtiradi.
    """
    # Loyiha nomi, versiyasi va API prefiksi
    PROJECT_NAME: str = "Task Manager API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # JWT Autentifikatsiyasi uchun maxfiy kalit va algoritmlar
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # Token amal qilish muddati (1 kun)

    # PostgreSQL ma'lumotlar bazasi ulanish parametrlari
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "task_user"
    POSTGRES_PASSWORD: str = "task_password"
    POSTGRES_DB: str = "task_db"
    TEST_POSTGRES_DB: str = "task_test_db"
    DATABASE_URL: Optional[str] = None

    @property
    def sync_database_url(self) -> str:
        """
        Asosiy PostgreSQL ma'lumotlar bazasiga ulanish satrini (DSN) hosil qiladi.
        SQLAlchemy 2.0 da psycopg2 drayveridan foydalaniladi.
        """
        if self.DATABASE_URL:
            if self.DATABASE_URL.startswith("postgresql://"):
                return self.DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
            return self.DATABASE_URL
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def test_database_url(self) -> str:
        """
        Avtomatik testlar (Pytest) uchun alohida test bazasiga ulanish satri.
        Imtihon talabi: Testlar alohida test bazasida yurgizilishi shart.
        """
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.TEST_POSTGRES_DB}"
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


# Barcha joyda qayta foydalanish uchun yagona sozlamalar obyekti
settings = Settings()
