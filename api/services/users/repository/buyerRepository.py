from fastapi import HTTPException, status
from typing import Optional
from dataclasses import astuple
from datetime import datetime, time

from deps import db_dependency
from services.users.model.buyerModel import Buyer
from services.users.utils import (
    BuyerFilter,
    PaginatedBuyerResponse,
    CreateBuyerInput,
    UpdateFilter,
    ToggleFilter,
)

from sqlalchemy import and_, or_


class BuyerRepository:
    def __init__(self, db_session: db_dependency):
        self.db = db_session

    def create_buyer(self, create_buyer_input: CreateBuyerInput) -> Buyer:
        db_buyer = Buyer(**create_buyer_input)
        self.db.add(db_buyer)
        self.db.commit()
        self.db.refresh(db_buyer)
        return db_buyer

    def fetch_buyer(self, buyer_id: Optional[str] = None, user_id: Optional[str] = None) -> Buyer:
        if not buyer_id and not user_id:
            raise ValueError('buyer_id and user_id not provided')

        query = self.db.query(Buyer)
        if buyer_id and user_id:
            query = query.filter(Buyer.id == buyer_id,
                                 Buyer.user_id == user_id)
        elif buyer_id:
            query = query.filter(Buyer.id == buyer_id)
        elif user_id:
            query = query.filter(Buyer.user_id == user_id)
        else:
            return None

        return query.first()

    def fetch_buyers(self, buyer_filter: Optional[BuyerFilter]) -> PaginatedBuyerResponse:
        search, is_active, is_deleted, created_at, skip, take = astuple(
            buyer_filter)

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
                        parsed_date = datetime.strptime(
                            cleaned_date, fmt).date()
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
            data=buyers,
            total=total_count,
            page=skip // take + 1 if take > 0 else 1,
            per_page=take,
            has_more=(skip + take) < total_count
        )

    def update_buyer(
        self,
        update_filter: UpdateFilter,
        user_id: Optional[str] = None,
        buyer_id: Optional[str] = None,
    ):
        if not buyer_id and not user_id:
            raise ValueError("either buyer_id or user_id must be provided")
        
        query_filter = []
        if buyer_id:
            query_filter.append(Buyer.id == buyer_id)
        if user_id:
            query_filter.append(Buyer.user_id == user_id)
        
        buyer = self.db.query(Buyer).filter(and_(*query_filter)).first()
        try:
            update_data = update_filter.model_dump(exclude_unset = True)
            for field, value in update_data.items():
                if hasattr(buyer, field) and value is not None:
                    setattr(buyer, field, value)

            buyer.updated_at = datetime.now()

            self.db.commit()
            self.db.refresh(buyer)

            return buyer
        except Exception as e:
            self.db.rollback()
            raise e
    
    def toggle_buyer(
            self,
            toggle_filter: ToggleFilter,
            buyer_id: Optional[str] = None,
            user_id: Optional[str] = None
    ):
        query_conditions = []
        if buyer_id:
            query_conditions.append(Buyer.id == buyer_id)

        if user_id:
            query_conditions.append(Buyer.user_id == user_id)
        
        if not buyer_id and not user_id:
            raise ValueError('buyer_id or user_id must be provided')
        
        buyer = self.db.query(Buyer).filter(and_(*query_conditions)).first()

        if not buyer:
            return None
        
        try:
            toggle_data = toggle_filter.model_dump(exclude_unset=True)
            # for field, value in toggle_data.items():
            #     if hasattr(buyer, field) and value is not None:
            #         setattr(buyer, field, value)
            if "is_active" in toggle_data and toggle_data["is_active"] is not None:
                buyer.is_active = not buyer.is_active
                buyer.updated_at = datetime.now()

            if "is_deleted" in toggle_data and toggle_data["is_deleted"] is not None:
                buyer.is_deleted = not buyer.is_deleted
                buyer.updated_at = datetime.now()

            self.db.commit()
            self.db.refresh(buyer)

            return buyer
        except Exception as e:
            self.db.rollback()
            raise e

        

        
