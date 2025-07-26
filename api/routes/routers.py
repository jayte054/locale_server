from .auth import router as auth_router
from .vendor import router as vendor_router

from fastapi import APIRouter


router = APIRouter()

router.include_router(auth_router)
router.include_router(vendor_router)
