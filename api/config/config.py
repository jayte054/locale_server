from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "DelPosh App"
    database_url: str = 'sqlite:///delposh_workouts_app.db'

    class Config:
        env_file = '.env'


settings = Settings()
