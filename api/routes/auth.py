from typing import Annotated
from routes.schema.schema import CreateUserSchema
from services.authService.utils import UserResponse, CreateUserRequest, RefreshResponse, LogoutResponse
from services.authService.authService import AuthService, SignInResponse
from fastapi.security import OAuth2PasswordRequestForm

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
    response_model=SignInResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {'description': "Bad Request"},
        408: {'description': "Request Timeout"}
    }
)
def sign_in(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], auth_service: AuthService = Depends(AuthService)):
    return auth_service.sign_in(form_data)

@router.post(
    '/refresh_token',
    response_model = RefreshResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {'description': "Bad Request"},
        408: {"description": "Bad Request"}
    }
)
def use_refresh_token(refresh_token: str, auth_service: AuthService = Depends(AuthService)):
    return auth_service.use_refresh_token(refresh_token)

@router.post(
    '/logout',
    response_model= LogoutResponse,
    status_code= status.HTTP_200_OK,
    responses={
        408: {'description': "Bad Request"}
    }
)
def logout(refresh_token: str, authService: AuthService = Depends(AuthService)):
    return authService.logout(refresh_token)