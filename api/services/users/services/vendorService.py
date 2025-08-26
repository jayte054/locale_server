from datetime import datetime, timezone, time
import logging
from dataclasses import astuple
from typing import Literal, Optional, Dict, Any
import pandas as pd
from io import StringIO, BytesIO

from deps import db_dependency, auth_dependency
from services.users.utils import (
    CreateVendorRequest,
    CreateVendorResponse,
    UpdateVendorInput,
    VendorFilter,
    FetchVendorResponse,
    VendorScale,
    VendorResponse,
)
from services.users.model.vendorModel import Vendor

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
                user_id=auth.get("id"),
                is_active = True,
                deleted = False,
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
                vendor_rating=vendor.vendor_rating,
                created_at=vendor.created_at.isoformat(),  # Convert datetime to string
                updated_at=vendor.updated_at.isoformat() if vendor.updated_at else None,
                vendor_metadata=vendor.vendor_metadata,
                is_active=vendor.is_active,
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

    def fetch_vendors(self, auth: auth_dependency, filter: Optional[VendorFilter] = None) -> FetchVendorResponse:
        if auth.get('role') != 'admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='user not an admin'
            )
        search, is_active, deleted, created_at, skip, take = astuple(filter)

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
        
        if is_active is not None:
            query = query.filter(Vendor.is_active == is_active)

        if deleted is not None:
            query = query.filter(Vendor.deleted == deleted)

        if created_at:
            try:
                # 2. Clean the input
                cleaned_date = created_at.strip()  # Remove whitespace
                
                # 3. Try multiple common date formats
                date_formats = [
                    '%d-%m-%y',  # 26-07-25
                    '%d-%m-%Y',  # 26-07-2025
                    '%Y-%m-%d',  # 2025-07-26 (ISO)
                    '%m/%d/%y',  # 07/26/25 (US format)
                    '%d.%m.%Y'   # 26.07.2025 (EU alternative)
                ]
                
                parsed_date = None
                for fmt in date_formats:
                    try:
                        parsed_date = datetime.strptime(cleaned_date, fmt).date()
                        break
                    except ValueError:
                        continue
                        
                if not parsed_date:
                    raise ValueError("No matching date format found")
                
                # 4. Filter using date range (most reliable method)
                start_dt = datetime.combine(parsed_date, time.min)
                end_dt = datetime.combine(parsed_date, time.max)
                
                query = query.filter(
                    Vendor.created_at >= start_dt,
                    Vendor.created_at <= end_dt
                )
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
        vendor_response = self.fetch_vendors(auth, filter)
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
            'vendor_location', 'created_at', 'vendor_scale',
            'is_active'
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
    
    def update_vendor(self, auth: auth_dependency, vendor_id: str, update_vendor_input: UpdateVendorInput) -> VendorResponse:
        (
        vendor_title, 
        vendor_location, 
        vendor_address, 
        vendor_contact, 
        vendor_email,
        vendor_merchandise,
        vendor_rating,
        vendor_scale,
        vendor_metadata
        ) = astuple(update_vendor_input)
        try:
            vendor = self.db.query(Vendor).filter(Vendor.id == vendor_id).first()
            
            if not vendor:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="vendor not found"
                )
            
            if vendor.user_id != auth.get("id"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="user not authorized to change detail"
                )
            # update_fields = update_vendor_input.model_dump(exclude_unset=True)
            vendor.vendor_title = vendor_title if vendor_title is not None else vendor.vendor_title
            vendor.vendor_location = vendor_location if vendor_location is not None else vendor.vendor_location
            vendor.vendor_address = vendor_address if vendor_address is not None else vendor.vendor_address
            vendor.vendor_contact = vendor_contact if vendor_contact is not None else vendor.vendor_contact
            vendor.vendor_email = vendor_email if vendor_email is not None else vendor.vendor_email
            vendor.vendor_merchandise = vendor_merchandise if vendor_merchandise is not None else vendor.vendor_merchandise
            vendor.vendor_rating = vendor_rating if vendor_rating is not None else vendor.vendor_rating
            vendor.vendor_scale = VendorScale(vendor_scale) if vendor_scale is not None else vendor.vendor_scale
            vendor.vendor_metadata = vendor_metadata if vendor_metadata is not None else vendor.vendor_metadata

            # for field, value in update_fields.items():
            #     if field == 'vendor_scale' and value is not None:
            #         setattr(vendor, field, VendorScale(value))
            #     else:
            #         setattr(vendor, field, value)

            vendor.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(vendor)

            logger.log('vendor updated successfully')
            return self.map_vendor_response(vendor)
        
        except HTTPException:
            raise
        except ValueError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=(status.HTTP_400_BAD_REQUEST),
                detail= f'invalid data; {str(e)}'
            ) from e
        except Exception as e:
            self.db.rollback()
            logger.error(
                'Error updating vendor %s: %s', 
                auth.get('id'), 
                str(e), 
                exc_info=True
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='failed to update vendor'
            ) from e
            

    def fetch_vendor(self, auth: auth_dependency, vendor_id: str) -> VendorResponse:
        try:
            vendor = self.db.query(Vendor).filter(
                Vendor.id == vendor_id,
                Vendor.user_id == auth.get('id')
                ).first()

            if not vendor:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail='vendor not found'
                )
            
            return self.map_vendor_response(vendor)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                'failed to fetch vendor %s: %s', 
                vendor_id, 
                str(e), 
                exc_info=True
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='failed to fetch vendor'
            ) from e
        
    def set_vendor_deletion_status(self, auth: auth_dependency, vendor_id: str, delete_status: bool, reason: str) -> VendorResponse:
        try:
            vendor = self.db.query(Vendor).filter(
                Vendor.id == vendor_id,
                Vendor.user_id == auth.get('id')
                ).first()
            
            if not vendor:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail='vendor not found'
                )
            
            vendor.deleted = delete_status
            vendor.updated_at = datetime.now(timezone.utc)

            vendor.vendor_metadata = {
                **vendor.vendor_metadata,
                'reason': reason
            }

            self.db.commit()
            self.db.refresh(vendor)
            return self.map_vendor_response(vendor)
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(
                'failed to delete vendor %s: %s', 
                vendor_id, 
                str(e), 
                exc_info=True
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='failed to delete vendor'
            ) from e
        
    def toggle_vendor_active_status(self, auth: auth_dependency, active_status: bool, vendor_id: str, reason: str) -> VendorResponse:
        if auth.get('role') != 'admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail= 'user is not an admin'
            )
        
        try:
            vendor = self.db.query(Vendor).filter(Vendor.id == vendor_id,).first()

            if not vendor:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail='vendor not found'
                )
            
            # vendor.is_active = active_status
            prev = vendor.is_active
            vendor.is_active =  not prev
            vendor.updated_at = datetime.now(timezone.utc)

            vendor.vendor_metadata = {
                **vendor.vendor_metadata,
                'reason_for_change_in_status': reason

            }

            self.db.commit()
            self.db.refresh(vendor)
            return self.map_vendor_response(vendor)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                'failed to deactivate vendor %s: %s', 
                vendor_id, 
                str(e), 
                exc_info=True
                )
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='failed to deactivate vendor'
            ) from e


    def map_vendor_response(self, vendor: Vendor) -> VendorResponse:
        return {
            "id": vendor.id,
            "vendor_title": vendor.vendor_title,
            "vendor_location": vendor.vendor_location,
            "vendor_address": vendor.vendor_address,
            "vendor_contact": vendor.vendor_contact,
            "vendor_email": vendor.vendor_email,
            "vendor_merchandise": vendor.vendor_merchandise,
            "vendor_scale": vendor.vendor_scale.value,  # Convert Enum to string
            "vendor_rating": vendor.vendor_rating,
            "created_at": vendor.created_at.isoformat(),  # Convert datetime to string
            "updated_at": vendor.updated_at.isoformat() if vendor.updated_at else None,
            "vendor_metadata": vendor.vendor_metadata,
            'is_active': vendor.is_active,
            'deleted': vendor.deleted,
            "userId": str(vendor.user_id),
        }
