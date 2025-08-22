
from services.users.utils import BuyerResponse, CreateBuyerRequest
from services.users.services.buyerService import BuyerService
from deps import auth_dependency

from fastapi import APIRouter, Depends


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