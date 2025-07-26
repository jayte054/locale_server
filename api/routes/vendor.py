
from services.userService.utils import CreateVendorResponse, CreateVendorRequest
from services.userService.vendorService import VendorService
from deps import auth_dependency

from fastapi import APIRouter, Depends


router = APIRouter(prefix="/vendor", tags=["Vendor"])

@router.post(
    '/create_vendor',
    response_model=CreateVendorResponse,
    responses={
        400: {'description': "Invalid input"},
        409: {"description": "vendor already exists for user profile"},
        500: {"description": "Internal server error"}
    }
)
def create_vendor(
    auth: auth_dependency, 
    create_vendor_request: CreateVendorRequest, 
    vendor_service: VendorService = Depends(VendorService),
    ):
    return vendor_service.create_vendor(auth, create_vendor_request)