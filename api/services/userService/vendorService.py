from datetime import datetime
import logging

from deps import db_dependency, auth_dependency
from services.userService.utils import CreateVendorRequest, CreateVendorResponse
from services.userService.model.vendorModel import Vendor

from dataclasses import astuple
from fastapi import HTTPException, status
from pydantic import TypeAdapter


logger = logging.getLogger(__name__)


class VendorService:
    def __init__(self, db_session: db_dependency):
        self.db = db_session

    def create_vendor(self, auth: auth_dependency, create_vendor_request: CreateVendorRequest) -> CreateVendorResponse:
        try:
            if self.db.query(Vendor).filter(Vendor.user_id == auth.get("id")).first():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="user already has a vendor profile"
                )

            vendor_data = create_vendor_request.model_dump()

            vendor = Vendor(
                **vendor_data,
                vendor_metadata={
                    "total_purchases": 0
                },
                vendor_rating=1,
                created_at=datetime.now(),
                user_id=auth.get("id")
            )

            self.db.add(vendor)
            self.db.commit()
            self.db.refresh(vendor)

            logger.info(f'vendor {vendor.vendor_title} created successfully')

            #    response_adapter = TypeAdapter(CreateVendorResponse)
            #    return response_adapter.validate_python(vendor.__dict__)

            return CreateVendorResponse(
                id=vendor.id,
                vendor_title=vendor.vendor_title,
                vendor_location=vendor.vendor_location,
                vendor_address=vendor.vendor_address,
                vendor_contact=vendor.vendor_contact,
                vendor_email=vendor.vendor_email,
                vendor_merchandise=vendor.vendor_merchandise,
                vendor_scale=vendor.vendor_scale.value,  # Convert Enum to string
                created_at=vendor.created_at.isoformat(),  # Convert datetime to string
                updated_at=vendor.updated_at.isoformat() if vendor.updated_at else None,
                vendor_metadata=vendor.vendor_metadata,
                userId=str(vendor.user_id)  # Explicitly map to userId field
            )
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f'Error creating vendor: {str(e)}', exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f'Error creating vendor: {str(e)}'
            ) from e
