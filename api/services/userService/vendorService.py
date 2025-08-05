from datetime import datetime
import logging
from dataclasses import astuple
from typing import Dict, Any, Literal
import pandas as pd
from io import StringIO, BytesIO

from deps import db_dependency, auth_dependency
from services.userService.utils import (
    CreateVendorRequest,
    CreateVendorResponse,
    VendorFilter,
    FetchVendorResponse,
)
from services.userService.model.vendorModel import Vendor

from pydantic import TypeAdapter
from sqlalchemy import or_, func
from fastapi import HTTPException, status, Depends
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors


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

            logger.info('vendor %s created successfully', vendor.vendor_title)

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
            logger.error('Error creating vendor: %s}', str(e), exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f'Error creating vendor: {str(e)}'
            ) from e

    def fetch_vendors(self, auth: auth_dependency, filter: VendorFilter) -> FetchVendorResponse:
        if auth.get('role') != 'admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='user not an admin'
            )
        search, created_at, skip, take = astuple(filter)

        default_skip = 0
        default_take = 50
        max_take = 500

        query = self.db.query(Vendor)

        if search:
            search_pattern = f'%{search}%'
            query = query.filter(
                or_(
                    Vendor.vendor_location.ilike(f'%{search_pattern}'),
                    Vendor.vendor_title.ilike(f'%{search_pattern}'),
                    Vendor.vendor_email.ilike(f'%{search_pattern}'),
                    Vendor.vendor_merchandise.ilike(f'%{search_pattern}'),
                    Vendor.vendor_scale.ilike(f'%{search_pattern}')
                )
            )

        if created_at:
            try:
                created_date = datetime.strptime(created_at, '%d-%m-%y').date()
                query = query.filter(
                    func.date(Vendor.created_at) == created_date)
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail='Invalid date format. Use DD-MM-YYYY'
                ) from exc

        skip = filter.skip if filter.skip is not None else default_skip
        take = filter.take if filter.take is not None else default_take

        if skip < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='skip should not be negative'
            )

        if take <= 0 or take > max_take:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Take must be between 1 and {max_take}"
            )

        total_count = query.count()

        query = query.offset(skip).limit(take)
        vendors = query.all()
        mapped_vendors = [self.map_vendor_response(v) for v in vendors]

        return FetchVendorResponse(
            data=mapped_vendors,
            total=total_count,
            page=skip // take + 1 if take > 0 else 1,
            per_page=take,
            has_more=(skip + take) < total_count
        )

    def export_vendors(self, format: Literal['csv', 'pdf'], auth: auth_dependency, filter: VendorFilter = Depends()):
        if auth.get('role') != 'admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='user not admin'
            )
        vendor_response = self.fetch_vendor(auth, filter)
        mapped_vendors = vendor_response.data

        if format == 'csv':
            return self.generate_csv(mapped_vendors)
        elif format == 'pdf':
            return self.generate_pdf(mapped_vendors)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid format. Choose 'csv' of pdf"
            )

    def generate_csv(self, mapped_vendors: list[dict]) -> StreamingResponse:
        df = pd.DataFrame(mapped_vendors)

        if 'created_at' in df.columns:
            df['created_at'] = pd.to_datetime(
                df['created_at']).dt.strftime('%d-%m-%y %H:%M:%S')

        stream = StringIO()
        df.to_csv(stream, index=False)

        return StreamingResponse(
            iter([stream.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=vendors_export.csv"}
        )

    def generate_pdf(self, mapped_vendors: list[dict]) -> StreamingResponse:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []

        pdf_fields = [
            'id', 'vendor_title', 'vendor_email',
            'vendor_location', 'created_at', 'vendor_scale'
        ]

        data = [pdf_fields]
        for vendor in mapped_vendors:
            data.append([str(vendor.get(field, '')) for field in pdf_fields])

        table = Table(data)
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ])
        table.setStyle(style)
        elements.append(table)

        #buld PDF
        doc.build(elements)
        buffer.seek(0)

        return StreamingResponse(
            buffer,
            media_type='application/pdf',
            headers={"Content-Disposition": "attachment; filename=vendors_export.pdf"}
        )

    def map_vendor_response(self, vendor: Vendor) -> Dict[str, Any]:
        return {
            "id": vendor.id,
            "vendor_title": vendor.vendor_title,
            "vendor_location": vendor.vendor_location,
            "vendor_address": vendor.vendor_address,
            "vendor_contact": vendor.vendor_contact,
            "vendor_email": vendor.vendor_email,
            "vendor_merchandise": vendor.vendor_merchandise,
            "vendor_scale": vendor.vendor_scale.value,  # Convert Enum to string
            "created_at": vendor.created_at.isoformat(),  # Convert datetime to string
            "updated_at": vendor.updated_at.isoformat() if vendor.updated_at else None,
            "vendor_metadata": vendor.vendor_metadata,
            "userId": str(vendor.user_id)
        }
