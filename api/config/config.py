from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()


class Settings(BaseSettings):
    app_name: str = os.getenv('APP_NAME')
    database_url: str = Field(default=os.getenv('DATABASE_URL'))
    auth_secret_key: str = Field(..., min_length=20)  # Required field
    auth_algorithm: str = Field(default=os.getenv('AUTH_ALGORITHM'))
    mailbox_api_key: str = Field(default=os.getenv('MAILBOX_API_KEY'))
    locale_email_address: str = os.getenv('LOCALE_EMAIL_ADDRESS')
    locale_email_password: str = os.getenv('LOCALE_EMAIL_PASSWORD')
    locale_smtp_host: str = os.getenv('LOCALE_SMTP_HOST')
    locale_smtp_port: str = os.getenv('LOCALE_SMTP_PORT')
    locale_frontend_url: str = os.getenv('LOCALE_FRONTEND_URL')

    class Config:
        env_file = '.env'
        extra = "forbid"


settings = Settings()
