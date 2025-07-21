from fastapi import FastAPI
from config.database import Base, engine
from config.config import settings
from routes.routers import router as api_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title=settings.app_name)

Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)


@app.get('/')
def health_check():
    return 'health check complete'


app.include_router(api_router)
