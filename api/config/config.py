from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Locale E-commerce App"
    database_url: str = 'sqlite:///locale_app.db'

    class Config:
        env_file = '.env'


settings = Settings()
