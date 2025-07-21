from typing import Annotated
from fastapi import Depends
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from config.database import SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated = 'auto', bcrypt__rounds = 12)