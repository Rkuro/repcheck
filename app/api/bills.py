from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from sqlalchemy import func
from typing import List
import logging
import traceback
from math import ceil
from ..database.database import get_session
from ..database.models import BillTable, BillWithVotes, PersonTable, PersonArea, VoteEvent
from pydantic import BaseModel

router = APIRouter(prefix="/api")
log = logging.getLogger(__name__)

class PaginatedBills(BaseModel):
    total_bills: int
    total_pages: int
    current_page: int
    page_size: int
    bills: List[BillWithVotes]

@router.get("/zipcodes/{zip_code}/bills", response_model=PaginatedBills)
def get_bills_for_representatives(
    zip_code: str,
    page: int = 1,
    page_size: int = 20,
    has_votes: bool = False,
    session: Session = Depends(get_session),
):
    """
    Fetch paginated bills for representatives associated with a given zip code.
    Optionally filter to only bills that have votes (has_votes=True).
    """
    try:
        area_id = f"ocd-division/country:us/zipcode:{zip_code}"

        # Validate page and page_size
        if page < 1 or page_size < 1:
            raise HTTPException(
                status_code=400, detail="page and page_size must be positive integers."
            )

        # Fetch person IDs from join table on zip code area IDs
        person_ids = (
            session.exec(
                select(PersonArea.person_id)
                .where(PersonArea.area_id == area_id)
                .distinct()
            )
            .all()
        )
        log.info(f"Found people {person_ids} for zip code {zip_code}")

        # Fetch their jurisdiction_area_ids
        jurisdiction_areas = session.exec(
            select(PersonTable.jurisdiction_area_id)
            .where(PersonTable.id.in_(person_ids))
            .distinct()
        ).all()
        jurisdiction_area_ids = [ja for ja in jurisdiction_areas]
        log.info(f"Found jurisdiction_area_ids {jurisdiction_area_ids}")

        # Build a base query for bills
        bills_query = (
            select(BillTable)
            .where(BillTable.jurisdiction_area_id.in_(jurisdiction_area_ids))
        )

        # If has_votes is True, only select bills that have at least one vote
        if has_votes:
            subquery_votes = select(VoteEvent.bill_id).distinct()
            bills_query = bills_query.where(BillTable.id.in_(subquery_votes))

        # Count total bills (with or without votes, depending on the filter above)
        total_bill_count = session.exec(
            select(func.count()).select_from(bills_query.subquery())
        ).one()
        log.info(f"Total bill count: {total_bill_count}")

        # Calculate total pages
        total_pages = ceil(total_bill_count / page_size)

        if page > total_pages and total_bill_count > 0:
            raise HTTPException(status_code=404, detail="Page not found.")

        # Query bills with pagination
        bills = (
            session.exec(
                bills_query.order_by(BillTable.latest_action_date.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            .all()
        )

        bill_ids = [bill.id for bill in bills]

        # Fetch votes for the returned bills
        votes = (
            session.exec(
                select(VoteEvent).where(VoteEvent.bill_id.in_(bill_ids))
            )
            .all()
        )
        log.info(f"Found {len(votes)} votes for bills {bill_ids}")

        # Attach votes to their respective bills
        bills_with_votes = []
        for bill in bills:
            bill_votes = [vote for vote in votes if vote.bill_id == bill.id]
            bills_with_votes.append(BillWithVotes(**bill.dict(), votes=bill_votes))

        return PaginatedBills(
            total_bills=total_bill_count,
            total_pages=total_pages,
            current_page=page,
            page_size=page_size,
            bills=bills_with_votes,
        )

    except Exception as e:
        log.exception(e)
        log.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail="Exception occurred when fetching bills for representatives."
        )



@router.get("/bills", response_model=BillWithVotes)
def get_bill(bill_id: str,  session: Session = Depends(get_session)):
    try:
        bill = session.exec(select(BillTable).where(BillTable.id == bill_id)).one_or_none()

        votes = session.exec(select(VoteEvent).where(VoteEvent.bill_id == bill.id)).all()
        bill_with_votes = BillWithVotes(**bill.dict(), votes=votes)

        log.info(f"Found bill {bill}")
        # if not bill:
        #     raise HTTPException(status_code=404, detail="Bill not found")
        
        return bill_with_votes
    except Exception as e:
        log.exception(e)
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Exception occurred when fetching bill.")