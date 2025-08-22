from typing import Literal, Dict, Any, Optional

from services.users.utils import (
    CreateVendorResponse, 
    CreateVendorRequest, 
    FetchVendorResponse,
    VendorFilter,
    UpdateVendorInput,
    VendorResponse,
    )
from services.users.services.vendorService import VendorService
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
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_deleted: Optional[bool] = None,
    created_at: Optional[str] = None,
    skip: int = 0,
    take: int = 50,
    vendor_service: VendorService = Depends(VendorService)
    ):
    filter = VendorFilter(
        search=search,
        is_active=is_active,
        is_deleted=is_deleted,
        created_at=created_at,
        skip=skip,
        take=take
    )
    return vendor_service.fetch_vendors(
        auth,
        filter
    )

@router.get(
    '/vendors/export/{format}',
    responses={400: {"description": "invalid format"}}
)
def export_vendors(
    format: Literal['csv', 'pdf'],
    auth: auth_dependency,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_deleted: Optional[bool] = None,
    created_at: Optional[str] = None,
    skip: int = 0,
    take: int = 50,
    vendor_service: VendorService = Depends(VendorService)
    ):
    filter = VendorFilter(
        search=search,
        is_active=is_active,
        is_deleted=is_deleted,
        created_at=created_at,
        skip=skip,
        take=take
    )
    return vendor_service.export_vendors(format, auth, filter)

@router.patch(
    '/update_vendor',
    response_model= VendorResponse,
    responses = {
        403: {"description": "user not authorized to change detail"},
        404: {'description': "vendor not found"},
        400: {'description': "invalid data"},
        500: {'description': 'failed to update vendor'}
    },
    summary='update vendor'
)
def update_vendor(
    auth: auth_dependency, 
    vendor_id: str,
    vendor_title: Optional[str] = None,
    vendor_location: Optional[str] = None,
    vendor_address: Optional[str] = None,
    vendor_contact: Optional[str] = None,
    vendor_email: Optional[str] = None,
    vendor_merchandise: Optional[str] = None,
    vendor_rating: Optional[str] = None,
    vendor_scale: Optional[str] = None,
    vendor_metadata: Optional[str] = None, 
    vendor_service: VendorService = Depends(VendorService)
    ):
    update_vendor_input = UpdateVendorInput(
        vendor_title = vendor_title,
        vendor_location = vendor_location,
        vendor_address = vendor_address,
        vendor_contact = vendor_contact,
        vendor_email = vendor_email,
        vendor_merchandise = vendor_merchandise,
        vendor_rating = vendor_rating,
        vendor_scale = vendor_scale,
        vendor_metadata = vendor_metadata
    )
    return vendor_service.update_vendor(
        auth,
        vendor_id,
        update_vendor_input,
    )

@router.get(
    'fetch_vendor',
    response_model= VendorResponse,
    responses= {
        404: {"description": "vendor not found"},
        500: {"description": "failed to fetch vendor"}
    },
    summary="fetch a single vendor"
)
def fetch_vendor(
    auth: auth_dependency, 
    vendor_id: str, 
    vendor_service: VendorService = Depends(VendorService)
    ):
    return vendor_service.fetch_vendor(auth, vendor_id)

@router.patch(
    '/delete_vendor',
    response_model= VendorResponse,
    responses= {
        404: {"description": "vendor not found"},
        500: {"description": "failed to delete vendor"}
    },
    summary= 'delete vendor'
)
def delete_vendor(
    auth: auth_dependency,
    vendor_id: str,
    delete_status: bool,
    reason: str,
    vendor_service: VendorService = Depends(VendorService)
    ) -> Dict[str, Any]:
    return vendor_service.set_vendor_deletion_status(
        auth,
        vendor_id,
        delete_status,
        reason
    )

@router.patch(
    'toggle_vendor_status',
    response_model= VendorResponse,
    responses = {
        403: {"description": "user is not admin"},
        404: {"description": "vendor not found"},
        500: {"description": "failed to deactivate vendor"}
    },
    summary= "toggle status of vendor by admin"
)
def toggle_vendor_active_status(
    auth: auth_dependency,
    active_status: bool,
    vendor_id: str,
    reason: str,
    vendor_service: VendorService = Depends(VendorService)
):
    return vendor_service.toggle_vendor_active_status(
        auth,
        active_status,
        vendor_id,
        reason
    )