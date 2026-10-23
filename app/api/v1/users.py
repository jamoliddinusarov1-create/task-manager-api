"""
Foydalanuvchi profili (Users) API yo'llari.
NIMA UCHUN KERAK:
- GET /users/me — Token orqali kirgan foydalanuvchining o'z profil ma'lumotlarini olish.
"""

from fastapi import APIRouter, Depends
from app.models.user import User
from app.schemas.user import UserResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Joriy foydalanuvchi profilini olish"
)
def get_my_profile(current_user: User = Depends(get_current_user)):
    """
    IMTIHON TALABI BO'YICHA:
    - Token orqali o'z profilini olish;
    - Muddati o'tgan yoki yaroqsiz token qat'iy rad etilsin (401 Unauthorized);
    - Password hash hech bir javobga kiritilmasin (UserResponse sxemasi bunga kafolat beradi).
    """
    return current_user
