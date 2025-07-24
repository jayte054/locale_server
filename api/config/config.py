from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    app_name: str = os.getenv('APP_NAME')
    database_url: str = Field(default=os.getenv('DATABASE_URL'))
    auth_secret_key: str = Field(..., min_length=20)  # Required field
    auth_algorithm: str = Field(default="HS256")

    class Config:
        env_file = '.env'
        extra = "forbid"


settings = Settings()
