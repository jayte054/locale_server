from typing import Optional

from services.users.utils import BuyerResponse, CreateBuyerRequest, PaginatedBuyerResponse, BuyerFilter
from services.users.services.buyerService import BuyerService
from deps import auth_dependency

from fastapi import APIRouter, Depends, Query


router = APIRouter(prefix="/buyer", tags=["Buyer"])


@router.post(
    '/create_buyer',
    response_model=BuyerResponse,
    responses={
        400: {'description': "Invalid input"},
        409: {"description": "vendor already exists for user profile"},
        500: {"description": "Internal server error"}
    }
)
def create_buyer(
    auth: auth_dependency,
    create_buyer_request: CreateBuyerRequest,
    buyer_service: BuyerService = Depends(BuyerService)
):
    return buyer_service.create_buyer(auth, create_buyer_request)


@router.get(
    '/fetch_buyer',
    response_model=BuyerResponse,
    responses={
        200: {"description": "Buyer fetched successfully"},
        400: {"description": "Invalid parameters"},
        401: {"description": "Not authenticated"},
        403: {"description": "Not authorized"},
        404: {"description": "Buyer not found"},
        500: {"description": "Internal server error"},
    },
    summary="Fetch buyer"
)
def fetch_buyer(
    auth: auth_dependency,
    buyer_id: Optional[str] = None,
    user_id: Optional[str] = None,
    buyer_service: BuyerService = Depends(BuyerService)
):
    return buyer_service.fetch_buyer(
        auth,
        buyer_id,
        user_id
    )


@router.get(
    '/fetch_buyers',
    response_model=PaginatedBuyerResponse,
    responses={
        200: {"description": "Buyers fetched successfully"},
        401: {"description": "Not authenticated"},
        403: {"description": "Not authorized"},
        500: {"description": "Internal server error"},
    },
    summary="fetch buyers"
)
def fetch_buyers(
    auth: auth_dependency,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_deleted: Optional[bool] = None,
    created_at: Optional[str] = None,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    take: int = Query(50, ge=1, le=500,
                      description="Number of records to return"),
    buyer_service: BuyerService = Depends(BuyerService)
):
    buyer_filter = BuyerFilter(
        search=search,
        is_active=is_active,
        is_deleted=is_deleted,
        created_at=created_at,
        skip=skip,
        take=take
    )
    return buyer_service.fetch_buyers(
        auth,
        buyer_filter
    )
