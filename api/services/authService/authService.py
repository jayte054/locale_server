import uuid
from datetime import timedelta, datetime, timezone
from typing import Annotated, Optional
import logging

from services.authService.model.authModel import User
from services.authService.model.blacklistModel import TokenBlacklist
from deps import bcrypt_context, db_dependency
from services.authService.utils import (
    CreateUserRequest, 
    LogoutResponse, 
    UserRole, 
    UserStatus, 
    UserResponse, 
    SignInResponse, 
    RefreshResponse, 
    UpdateUserInterface
    )
from dataclasses import astuple
from jose import jwt, JWTError
from sqlalchemy.exc import SQLAlchemyError
from fastapi import Body, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from config.config import settings


SECRET_KEY = settings.auth_secret_key
ALGORITHM = settings.auth_algorithm

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, db_session: db_dependency):
        self.db = db_session

    def create_user(self, create_user_request: CreateUserRequest) -> UserResponse:
        first_name, last_name, email, phone_number, password = astuple(
            create_user_request)
        try:
            if self.db.query(User).filter(User.email == email).first():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail='email already exists'
                )

            if not all([first_name, last_name, email, phone_number, password]):
                missing_fields = []
                if not first_name:
                    missing_fields.append('first name')
                if not phone_number:
                    missing_fields.append('phone number')
                if not password:
                    missing_fields.append('password')
                if not email:
                    missing_fields.append('email')
                if not last_name:
                    missing_fields.append('last name')

                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f'Missing required fields: {', '.join(missing_fields)}'
                )

            user = User(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone_number=phone_number,
                hashed_password=bcrypt_context.hash(password),
                created_at=datetime.now(),
                role=UserRole.User,
                user_active=True,
                user_status=UserStatus.New_User,
                user_metadata={}
            )

            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

            logger.info(f'user {user.first_name} created successfully')
            return UserResponse(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone_number=phone_number,
                created_at=datetime.now(),
                role=UserRole.User,
                user_active=True,
                user_status=UserStatus.New_User,
                user_metadata={}
            )

        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f'Error creating user: {str(e)}'
            ) from e

    def authenticate_user(self, email: str, password: str):
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail='could not validate user'
            )
        if not bcrypt_context.verify(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='incorrect password'
            )
        if not user.user_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='user account is inactive'
            )
        return user

    def create_access_token(self, email: str, user_id: str, expires_delta: timedelta):
        try:
            encode = {
                'sub': email, 
                'id': user_id, 
                'jti': str(uuid.uuid4()),
                'token_type': 'access',
                'iat': datetime.now(timezone.utc)
                }
            expires_in = datetime.now(timezone.utc) + expires_delta
            encode.update({"exp": expires_in})
            return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f'token creation failed: {str(e)}'
            )

    def create_refresh_token(self, user_id: str, expires_delta=timedelta):
        try:
            expires_in = datetime.now(timezone.utc) + expires_delta
            payload = {
                'sub': 'refresh',
                'id': user_id,
                'exp': expires_in,
                'token_type': 'refresh'
            }
            token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
            return token
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f'failed to create refresh token: {str(e)}'
            )

    def sign_in(self, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> SignInResponse:
        try:
            user = self.authenticate_user(form_data.username, form_data.password)
            token = self.create_access_token(
                user.email, user.id, timedelta(minutes=40))
            refresh_token = self.create_refresh_token(
                user.id, timedelta(days=3))
            
            current_metadata = user.user_metadata or {}
            update_data = {
                "user_metadata": {
                    **current_metadata,
                    "last_sign_in": datetime.now().isoformat()
                },
                "user_active": True
            }

            if user.user_status == UserStatus.New_User:
                update_data['user_status']= UserStatus.Active_User

                
            self.update_user(user, UpdateUserInterface(**update_data))

            return SignInResponse(
                user={
                    "email": user.email,
                    "name": f'{user.first_name} {user.last_name}',
                    "id": user.id,
                    "contact": user.phone_number,
                    "role": user.role,
                    "status": user.user_status,
                    "metadata": user.user_metadata,
                },
                access_token=token,
                refresh_token=refresh_token,
                token_type='bearer',
                access_token_expires_in=2400,
                refresh_token_expires_in=14400
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f'authentication failed: {str(e)}'
            )

    def use_refresh_token(self, refresh_token: str = Body(..., embed=True)) -> RefreshResponse:
        try:
            if self.is_token_revoked(refresh_token):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='token already revoked'
                )

            payload = jwt.decode(
                refresh_token,
                SECRET_KEY,
                algorithms=ALGORITHM
            )
            
            if payload.get('token_type') != 'refresh':
                raise HTTPException(
                    status_code=400,
                    detail='invalid token'
                )
            user_id = payload.get('id')
            user = self.db.query(User).filter(User.id == user_id).first()

            if not user or not user.user_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='user not found or inactive'
                )

            access_token = self.create_access_token(
                user.email, user.id, timedelta(minutes=40))
            new_refresh_token = self.create_refresh_token(
                user_id, timedelta(days=3))
            
            self.revoke_token(refresh_token)

            return RefreshResponse(
                access_token = access_token,
                refresh_token = new_refresh_token,
            )
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f'invalid refresh token, {str(e)}'
            )

    def revoke_token(self, token: str) -> str:
        print(token)
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

            if datetime.fromtimestamp(payload['exp']) < datetime.utcnow():
                return

            if self.is_token_revoked(token):
                return 'token already revoked'

            blacklisted = TokenBlacklist(
                token=token,
                user_id=payload.get('id'),
                expires=datetime.fromtimestamp(payload['exp'])
            )
            self.db.add(blacklisted)
            self.db.commit()
            return 'token successfully revoked'

        except JWTError as e:
            raise ValueError(f'Invalid token: {str(e)}') from e
        except SQLAlchemyError as e:
            self.db.rollback()
            raise RuntimeError(f'database error: {str(e)}') from e

    def is_token_revoked(self, token: str) -> bool:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

            blacklisted = self.db.query(TokenBlacklist).filter(
                TokenBlacklist.user_id == payload.get('id'),
                TokenBlacklist.token == token,
                TokenBlacklist.expires >= datetime.utcnow()
            ).first()

            return blacklisted is not None
        except JWTError:
            return True

    def logout(self, refresh_token: Optional[str] = None) -> LogoutResponse:
        try:
            refresh_token and self.revoke_token(refresh_token)

            return LogoutResponse(
                status='success',
                message='successfully logged out',
                timestamp=datetime.utcnow().isoformat()
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f'logout failed: {str(e)}'
            )
        
    def update_user(self, user: User, input: UpdateUserInterface):
        try:
            field_updates = {
                'user_status': input.user_status,
                'user_active': input.user_active,
                'user_metadata': input.user_metadata,
                'phone_number': input.phone_number,
                'email': input.email,
            }

            for field, value in field_updates.items():
                if value is not None:
                    setattr(user, field, value)

            self.db.commit()
            self.db.refresh(user)

            return {"ok": True}
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f'Database error: {str(e)}'
            )

