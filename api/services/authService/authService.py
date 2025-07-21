from services.authService.model.userModel import User
from deps import bcrypt_context, db_dependency
from services.authService.utils import CreateUserRequest, UserRole, UserStatus, UserResponse
from dataclasses import astuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status



class AuthService:
    def __init__(self, db_session: db_dependency):
        self.db = db_session

    def create_user(self, create_user_request: CreateUserRequest) -> UserResponse:
        name, phone_number, password = astuple(create_user_request)
        try:
            if self.db.query(User).filter(User.name == name).first():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail='username already exists'
                )
            
            if not all([name, phone_number, password]):
                missing_fields = []
                if not name:
                    missing_fields.append('name')
                if not phone_number:
                    missing_fields.append('phone number')
                if not password:
                    missing_fields.append('password')

                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f'Missing required fields: {', '.join(missing_fields)}'
                )

            user = User(
                name=name,
                phone_number=phone_number,
                hashed_password=bcrypt_context.hash(password),
                role=UserRole.User,
                user_active=True,
                user_status=UserStatus.NOT_PAID,
                user_metadata={}
            )

            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user

        except HTTPException:
            raise
        except Exception as e: 
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f'Error creating user: {str(e)}'
            ) from e

    def authenticate_user(self, username: str, password: str):
        user = self.db.query(User).filter(User.username == username).first()
        if not user:
            return False
        if not bcrypt_context.verify(password, user.hashed_password):
            return False
        return User
