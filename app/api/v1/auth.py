"""
Autentifikatsiya (Ro'yxatdan o'tish va Login) API yo'llari (Routers).
NIMA UCHUN KERAK:
- POST /auth/register — Yangi foydalanuvchini ro'yxatdan o'tkazish;
- POST /auth/login — Login va parol orqali JWT access token olish.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import UserCreate, UserResponse
from app.schemas.token import Token
from app.crud.crud_user import get_user_by_email, create_user, authenticate_user
from app.core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yangi foydalanuvchini ro'yxatdan o'tkazish"
)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    IMTIHON TALABI BO'YICHA:
    - Email takrorlanmasligi tekshiriladi (takrorlansa 400 xatolik);
    - Parol bcrypt orqali xeshlangan holda saqlanadi;
    - Oddiy ro'yxatdan o'tishda yuqori huquqli rol berilmaydi;
    - Response da parol xeshi qaytarilmaydi.
    """
    existing_user = get_user_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )

    user = create_user(db, user_in=user_in)
    return user


@router.post(
    "/login",
    response_model=Token,
    summary="Login qilish va JWT access token olish",
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "email": {"type": "string", "format": "email", "example": "jamoliddin@example.com"},
                            "password": {"type": "string", "format": "password", "example": "StrongPassword123!"}
                        },
                        "required": ["email", "password"]
                    }
                },
                "application/x-www-form-urlencoded": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "username": {"type": "string", "description": "Email address"},
                            "password": {"type": "string", "description": "Password"}
                        },
                        "required": ["username", "password"]
                    }
                }
            }
        }
    }
)
async def login(request: Request, db: Session = Depends(get_db)):
    """
    IMTIHON TALABI BO'YICHA:
    - To'g'ri login va parolga amal qilish muddati bor JWT access token qaytarish;
    - Noto'g'ri login yoki parolga qat'iy 401 Unauthorized qaytarish;
    - Swagger UI da bevosita JSON yoki Form data orqali ishlash imkoniyati mavjud.
    """
    content_type = request.headers.get("content-type", "")
    username = None
    password = None

    if "application/json" in content_type:
        try:
            body = await request.json()
            username = body.get("email") or body.get("username")
            password = body.get("password")
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid JSON payload"
            )
    else:
        form = await request.form()
        username = form.get("username") or form.get("email")
        password = form.get("password")

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Email (or username) and password are required"
        )

    user = authenticate_user(db, email=str(username), password=str(password))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    access_token = create_access_token(subject=user.id)
    return Token(access_token=access_token, token_type="bearer")
