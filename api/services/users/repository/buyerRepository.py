from fastapi import HTTPException, status
from typing import Optional
from dataclasses import astuple
from datetime import datetime, time
from deps import db_dependency
from services.users.utils import CreateBuyerInput
from services.users.model.buyerModel import Buyer
from services.users.utils import BuyerFilter, PaginatedBuyerResponse

from sqlalchemy import or_

class BuyerRepository:
    def __init__(self, db_session: db_dependency):
        self.db = db_session

    def create_buyer(self, create_buyer_input: CreateBuyerInput) -> Buyer:
        db_buyer = Buyer(**create_buyer_input)
        self.db.add(db_buyer)
        self.db.commit()
        self.db.refresh(db_buyer)
        return db_buyer

    
    def fetch_buyer(self, buyer_id: str, user_id: str) -> Buyer:
        return self.db.query(Buyer).filter(
            Buyer.id == buyer_id,
            Buyer.user_id == user_id
            ).first()

    def fetch_buyers(self, filter: Optional[BuyerFilter]) -> PaginatedBuyerResponse:
        search, is_active, is_deleted, created_at, skip, take = astuple(filter)

        query = self.db.query(Buyer)

        if search:
            search_pattern = f'%{search}%'
            query = query.filter(
                or_(
                    Buyer.buyer_location.ilike(f'%{search_pattern}'),
                    Buyer.buyer_address.ilike(f'%{search_pattern}'),
                    Buyer.buyer_email.ilike(f'%{search_pattern}'),
                    Buyer.buyer_name.ilike(f'%{search_pattern}')
                )
            )

        if is_active is not None:
            query = query.filter(Buyer.is_active == is_active)

        if is_deleted is not None:
            query = query.filter(Buyer.is_deleted == is_deleted)

        if created_at:
            try:
                cleaned_date = created_at.strip()

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
                    raise ValueError("No matching date fomrat found")
                
                start_date = datetime.combine(parsed_date, time.min)
                end_date = datetime.combine(parsed_date, time.max)

                query = query.filter(
                    Buyer.created_at >= start_date,
                    Buyer.created_at <= end_date
                )
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="invalid date format. use DD-MM-YYY"
                ) from exc
            
        total_count = query.count()

        query = query.offset(skip).limit(take)
        buyers = query.all()

        return PaginatedBuyerResponse(
            data = buyers,
            total = total_count,
            page = skip // take + 1 if take > 0 else 1,
            per_page = take,
            has_more = (skip + take) < total_count
        )
