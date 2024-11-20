from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from sqlalchemy import func
from typing import List
import logging
import traceback
from math import ceil
from ..database.database import get_db
from ..database.models import Bill, ZipcodePeopleJoinTable, Person
from pydantic import BaseModel

router = APIRouter(prefix="/api")
log = logging.getLogger(__name__)

class PaginatedBills(BaseModel):
    total_bills: int
    total_pages: int
    current_page: int
    page_size: int
    bills: List[Bill]

@router.get("/zipcodes/{zip_code}/bills", response_model=PaginatedBills)
def get_bills_for_representatives(
    zip_code: str,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    try:
        # Validate page and page_size
        if page < 1 or page_size < 1:
            raise HTTPException(
                status_code=400, detail="page and page_size must be positive integers."
            )

        # Fetch jurisdiction IDs for people associated with the zip code
        jurisdiction_ids = set(
            db.exec(
                select(Person.jurisdiction_id)
                .join(ZipcodePeopleJoinTable)
                .where(ZipcodePeopleJoinTable.zip_code == zip_code)
            )
            .all()
        )
        log.info(f"Found jurisdictions {jurisdiction_ids} for zip code {zip_code}")

        
        total_bill_count = db.exec(
            select(func.count())
            .select_from(Bill)
            .where(Bill.jurisdiction_id.in_(jurisdiction_ids))
        ).one()
        log.info(f"Total bill count: {total_bill_count}")

        total_pages = ceil(total_bill_count / page_size)

        if page > total_pages and total_bill_count > 0:
            raise HTTPException(status_code=404, detail="Page not found.")

        # Query bills with pagination
        bills = (
            db.exec(
                select(Bill)
                .where(Bill.jurisdiction_id.in_(jurisdiction_ids))
                .order_by(Bill.updated_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            ).all()
        )

        return PaginatedBills(
            total_bills=total_bill_count,
            total_pages=total_pages,
            current_page=page,
            page_size=page_size,
            bills=bills,
        )
        
        
    except Exception as e:
        log.exception(e)
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Exception occurred when fetching bills for representatives.")



@router.get("/bills", response_model=Bill)
def get_bill(bill_id: str,  db: Session = Depends(get_db)):
    try:
        bill = db.exec(select(Bill).where(Bill.id == bill_id)).one_or_none()

        log.info(f"Found bill {bill}")
        # if not bill:
        #     raise HTTPException(status_code=404, detail="Bill not found")
        
        return bill
    except Exception as e:
        log.exception(e)
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Exception occurred when fetching bill.")