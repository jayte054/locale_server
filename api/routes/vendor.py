from typing import Literal

from services.userService.utils import (
    CreateVendorResponse, 
    CreateVendorRequest, 
    FetchVendorResponse,
    VendorFilter,
    )
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

@router.get(
    '/fetch_vendors',
    response_model=FetchVendorResponse,
    responses= {
        403: {"description": "user not admin"},
        400: {"description": "Bad Request"}
    },
    summary="Fetch paginated vendors"
)
def fetch_vendors(
    auth: auth_dependency, 
    filter: VendorFilter,
    vendor_service: VendorService = Depends(VendorService)
    ):
    return vendor_service.fetch_vendors(
        auth,
        filter
    )

@router.get(
    '/vendors/export/{format}',
    responses={400: "description": "invalid format"}
)
def export_vendors(
    format: Literal['csv', 'pdf'],
    auth: auth_dependency,
    filter: VendorFilter,
    vendor_service: VendorService = Depends(VendorService)
    ):
    return vendor_service.export_vendors(format, auth, filter)