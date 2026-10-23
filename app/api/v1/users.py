from fastapi import APIRouter, Depends
from app.models.user import User
from app.schemas.user import UserResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile"
)
def get_my_profile(current_user: User = Depends(get_current_user)):
    """
    Retrieve profile of the currently authenticated user.
    Password hash is never included in the response.
    Invalid or expired tokens return 401 Unauthorized.
    """
    return current_user
