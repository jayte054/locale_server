from routes.schema.schema import CreateUserSchema
from services.authService.utils import UserResponse, CreateUserRequest
from services.authService.authService import AuthService

from fastapi import APIRouter, status, Depends


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    '/register',
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Invalid input"},
        409: {"description": "Username already exists"},
        500: {"description=": "Internal server error"}
    }
)
def register_user(user_data: CreateUserRequest, auth_service: AuthService = Depends(AuthService)):
    return auth_service.create_user(user_data)

@router.post(
    '/sign_in',
    response_model=
)
