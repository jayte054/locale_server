import logging
from typing import Optional
from dataclasses import astuple

from deps import db_dependency, auth_dependency
from services.users.utils import (
    CreateBuyerRequest,
    CreateBuyerInput,
    BuyerResponse,
    BuyerFilter,
    PaginatedBuyerResponse,
    UpdateFilter,
    ToggleFilter,
)
from services.users.model.buyerModel import Buyer
from services.users.repository.buyerRepository import BuyerRepository

from fastapi import HTTPException, status
from datetime import datetime

logger = logging.getLogger(__name__)


class BuyerService:
    def __init__(self, db_session: db_dependency):
        self.db = db_session
        self.buyerRepo = BuyerRepository(db_session)

    def create_buyer(self, auth: auth_dependency, create_buyer_request: CreateBuyerRequest) -> BuyerResponse:
        try:
            user_id = auth.get("id")
            if self.buyerRepo.fetch_buyer(user_id=user_id):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="buyer already exists"
                )

            buyer_data = create_buyer_request.model_dump()

            create_buyer_input = CreateBuyerInput(
                **buyer_data,
                buyer_email=auth.get("email"),
                buyer_contact=auth.get("phone_number"),
                created_at=datetime.now(),
                is_active=True,
                is_deleted=False,
                buyer_metadata={
                    "total_purchased": 0
                },
                user_id=auth.get("id")
            )

            buyer: Buyer = self.buyerRepo.create_buyer(create_buyer_input)

            logger.info('buyer %s created successfully', buyer.id)

            return BuyerResponse(
                id=buyer.id,
                buyer_name=buyer.buyer_name,
                buyer_email=buyer.buyer_email,
                buyer_location=buyer.buyer_location,
                buyer_address=buyer.buyer_address,
                buyer_contact=buyer.buyer_contact,
                created_at=buyer.created_at,
                updated_at=buyer.updated_at,
                is_active=buyer.is_active,
                is_deleted=buyer.is_deleted,
                buyer_metadata=buyer.buyer_metadata,
                user_id=buyer.user_id
            )
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error('Error creating buyer: %s', str(e), exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f'Error creating buyer: {str(e)}'
            ) from e

    def fetch_buyer(
            self,
            auth: auth_dependency,
            buyer_id: Optional[str] = None,
            user_id: Optional[str] = None
    ) -> BuyerResponse:
        user_id = auth.get("id")
        buyer_filter = {}
        try:
            if buyer_id:
                buyer_filter["buyer_id"] = buyer_id
            if user_id:
                buyer_filter["user_id"] = user_id
            if not buyer_filter:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="user_id and buyer_id not provided"
                )
            buyer = self.buyerRepo.fetch_buyer(**buyer_filter)

            if not buyer:
                logger.error('buyer with userId %s not found', buyer_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail='buyer not found'
                )

            logger.log('buyer with userid %s fetched successfully', buyer_id)
            return self.map_to_buyer_response(buyer)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                'failed to fetch vendor %s: %s',
                buyer_id,
                str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='failed to fetch buyer'
            ) from e

    def fetch_buyers(self, auth: auth_dependency, buyer_filter: BuyerFilter) -> PaginatedBuyerResponse:
        if auth.get('role') != "admin":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='user not authorized'
            )

        search, is_active, is_deleted, created_at, skip, take = astuple(
            buyer_filter)
        max_take = 500

        if skip < 0:
            skip = 0

        if take <= 0 or take > max_take:
            take = 50

        # filtered_filter: BuyerFilter = {
        #     **({"search": search} if search is not None and search.strip() else {}),
        #     **({"is_active": is_active} if is_active is not None else {}),
        #     **({"is_deleted": is_deleted} if is_deleted is not None else {}),
        #     **({"created_at": created_at} if created_at is not None else {}),
        #     "skip": skip,
        #     "take": take
        # }

        filtered_filter = BuyerFilter(
            search=search if search and search.strip() else None,
            is_active=is_active,
            is_deleted=is_deleted,
            created_at=created_at,
            skip=skip,
            take=take
        )

        buyers = self.buyerRepo.fetch_buyers(filtered_filter)
        mapped_buyers = [self.map_to_buyer_response(
            buyer) for buyer in buyers.data]

        logger.log('buyer fetched successfully buy user', auth.get('id'))
        return PaginatedBuyerResponse(
            data=mapped_buyers,
            total=buyers.total,
            page=buyers.page,
            per_page=buyers.per_page,
            has_more=buyers.has_more
        )

    def update_buyer_by_admin(
            self,
            auth: auth_dependency,
            update_filter: UpdateFilter,
            buyer_id: str
    ):
        if auth.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="unauthorized access"
            )

        try:
            updated_buyer = self.buyerRepo.update_buyer(
                update_filter=update_filter, 
                buyer_id=buyer_id
                )

            if not updated_buyer:
                logger.error('failed to update buyer %s', buyer_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="failed to update buyer"
                )

            logger.info('buyer updated successfully %s', buyer_id)
            return self.map_to_buyer_response(updated_buyer)
        except HTTPException:
            raise
        except Exception as e:
            logger.error("failed to update buyer %s: %s",
                         buyer_id, str(e), exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="failed to update buyer"
            ) from e

    def update_buyer(
            self,
            auth: auth_dependency,
            update_filter: UpdateFilter,
    ):
        user_id = auth.get("id")
        try:
            updated_buyer = self.buyerRepo.update_buyer(
                update_filter=update_filter,
                user_id=user_id
            )

            if not updated_buyer:
                logger.error("failed to update buyer %s", user_id)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail='buyer not found'
                )

            logger.info("buyer updated successfully %s", user_id)
            return self.map_to_buyer_response(updated_buyer)
        except HTTPException:
            raise
        except Exception as e:
            logger.error("failed to update buyer %s: %s",
                         user_id, str(e), exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="failed to update buyer"
            ) from e

    def update_buyer_service(
            self,
            update_filter: UpdateFilter,
            buyer_id: Optional[str] = None,
            user_id: Optional[str] = None,
    ):
        target_id: str

        try:
            if buyer_id:
                updated_buyer = self.buyerRepo.update_buyer(
                    update_filter=update_filter, 
                    buyer_id = buyer_id
                    )
                target_id = buyer_id
            else:
                updated_buyer = self.buyerRepo.update_buyer(
                    update_filter=update_filter,
                    user_id=user_id
                )
                target_id = user_id
            
            if not updated_buyer:
                logger.error('buyer not found %s', target_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail='buyer not found'
                )
            
            logger.info("Buyer %s successfully updated", target_id)
            return self.map_to_buyer_response(updated_buyer)
        except HTTPException:
            raise
        except Exception as e:
            logger.error('failed to update buyer %s', target_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="failed to update buyer"
            )



    def toggle_buyer_admin(
            self,
            auth: auth_dependency,
            toggle_filter: ToggleFilter,
            buyer_id: str
    ):
        if auth.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="unauthorized access"
            )
        user_id = auth.get("id")

        try:
            toggled_buyer = self.buyerRepo.toggle_buyer(
                toggle_filter=toggle_filter,
                buyer_id=buyer_id
            )

            if not toggled_buyer:
                logger.error("buyer not found, buyer: %s", buyer_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=("buyer %s not found", buyer_id)
                )

            logger.info("buyer %s status successfully toggled by %s", buyer_id, user_id)
            return self.map_to_buyer_response(toggled_buyer)
        except HTTPException:
            raise
        except Exception as e:
            logger.error("failed to toggle buyer %s by admin %s : %s",
                         buyer_id, user_id, str(e), exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="failed to toggle buyer status"
            ) from e

    def toggle_buyer(
            self,
            auth: auth_dependency,
            toggle_filter: ToggleFilter
    ):
        user_id = auth.get("id")

        try:
            toggled_buyer = self.buyerRepo.toggle_buyer(
                toggle_filter=toggle_filter,
                user_id=user_id
            )

            if not toggled_buyer:
                logger.error("failed to toggle buyer %s", user_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="failed to update buyer"
                )

            logger.info("buyer %s status successfully toggled", user_id)
            return self.map_to_buyer_response(toggled_buyer)
        except HTTPException:
            raise
        except Exception as e:
            logger.error("failed to toggle buyer %s status: %s",
                         user_id, str(e), exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="failed to toggle buyer status"
            ) from e


    def toggle_buyer_service(
        self,
        auth: auth_dependency,
        toggle_filter: ToggleFilter,
        buyer_id: Optional[str] = None
    ):
        user_id = auth.get("id")

        # Admin can toggle any buyer, regular users can only toggle themselves
        if buyer_id and auth.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required to toggle other buyers"
            )

        target_id = buyer_id if buyer_id else user_id

        try:
            toggled_buyer = self.buyerRepo.toggle_buyer(
                toggle_filter=toggle_filter,
                buyer_id=target_id
            )

            if not toggled_buyer:
                logger.error("Buyer not found: %s", target_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Buyer not found"
                )

            logger.info("Buyer %s status toggled by user %s",
                        target_id, user_id)
            return self.map_to_buyer_response(toggled_buyer)

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to toggle buyer %s: %s",
                        target_id, str(e), exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to toggle buyer status"
            ) from e

    def map_to_buyer_response(self, buyer: Buyer) -> BuyerResponse:
        return {
            "id": buyer.id,
            "buyer_name": buyer.buyer_name,
            "buyer_email": buyer.buyer_email,
            "buyer_location": buyer.buyer_location,
            "buyer_address": buyer.buyer_address,
            "buyer_contact": buyer.buyer_contact,
            "created_at": buyer.created_at,
            "updated_at": buyer.updated_at,
            "is_active": buyer.is_active,
            "is_deleted": buyer.is_deleted,
            "buyer_metadata": buyer.buyer_metadata,
            "user_id": buyer.user_id
        }
