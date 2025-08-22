from contextlib import asynccontextmanager
from config.database import Base, engine, SessionLocal
from config.config import settings
from services.authService.model.authModel import User
from services.authService.model.blacklistModel import TokenBlacklist
from services.users.model.vendorModel import Vendor
from deps import TokenCleanUpScheduler
from routes.routers import router as api_router
from fastapi.middleware.cors import CORSMiddleware

from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage start up and shutdown events"""
    #startup    
    Base.metadata.create_all(bind=engine)
    scheduler_db = SessionLocal()
    scheduler = TokenCleanUpScheduler(scheduler_db)
    scheduler.start()

    app.state.scheduler = scheduler
    app.state.scheduler_db = scheduler_db
    yield

    #shutdown
    scheduler.shutdown()
    scheduler_db.close()


app = FastAPI(title=settings.app_name, lifespan=lifespan)


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
