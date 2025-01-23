from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from sqlalchemy import func, desc, asc, or_, text
from sqlalchemy.dialects.postgresql import JSONB
from typing import List, Optional
from datetime import date
import logging
import json
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
    # --- New filters ---
    date_type: Optional[str] = None,  # e.g. "latest_action_date" or "creation_date"
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    jurisdiction_level: Optional[str] = None,  # e.g. "federal" | "state" | "local"

    # Allow multiple representative IDs
    # Example usage: ?representative_ids=rep1&representative_ids=rep2
    representative_ids: Optional[List[str]] = Query(default=None),

    # --- Sorting ---
    sort_by: str = "latest_action_date",  # "creation_date", "latest_action_date", "latest_vote_date", "title"
    sort_order: str = "desc",            # "asc" or "desc"

    session: Session = Depends(get_session),
):
    """
    Fetch paginated bills for representatives associated with a given zip code,
    with optional filters and sorting:
      - Filter by date range (using either latest_action_date or creation_date).
      - Filter by jurisdiction_level.
      - Filter by has_votes (already present).
      - Filter by multiple representative_ids who have voted on the bill.
      - Sort by creation_date, latest_action_date, latest_vote_date, or title.
    """

    try:
        area_id = f"ocd-division/country:us/zipcode:{zip_code}"

        # Validate pagination
        if page < 1 or page_size < 1:
            raise HTTPException(
                status_code=400,
                detail="page and page_size must be positive integers."
            )

        # Find person_ids for this zip code
        person_ids = (
            session.exec(
                select(PersonArea.person_id)
                .where(PersonArea.area_id == area_id)
                .distinct()
            )
            .all()
        )
        log.info(f"Found people {person_ids} for zip code {zip_code}")

        # Find jurisdiction_area_ids for these people
        jurisdiction_areas = session.exec(
            select(PersonTable.jurisdiction_area_id)
            .where(PersonTable.id.in_(person_ids))
            .distinct()
        ).all()
        jurisdiction_area_ids = [ja for ja in jurisdiction_areas]
        log.info(f"Found jurisdiction_area_ids {jurisdiction_area_ids}")

        # Base query: bills for those jurisdiction areas
        bills_query = select(BillTable).where(BillTable.jurisdiction_area_id.in_(jurisdiction_area_ids))

        # Optional filter: bills that have at least one vote (has_votes=True)
        if has_votes:
            subquery_votes = select(VoteEvent.bill_id).distinct()
            bills_query = bills_query.where(BillTable.id.in_(subquery_votes))

        # Optional filter: jurisdiction_level
        if jurisdiction_level:
            bills_query = bills_query.where(BillTable.jurisdiction_level == jurisdiction_level)

        # Optional filter: date range on either creation_date or latest_action_date
        if date_type in ["latest_action_date", "creation_date"]:
            if date_type == "latest_action_date":
                date_column = BillTable.latest_action_date
            else:
                date_column = BillTable.created_at

            if start_date:
                bills_query = bills_query.where(date_column >= start_date)
            if end_date:
                bills_query = bills_query.where(date_column <= end_date)
        else:
            raise HTTPException(status_code=400, detail="date_type must be 'latest_action_date' or 'creation_date'")

        # Optional filter: one or more representative IDs who have voted on it
        # We'll do an OR condition so that if a bill has a vote from *any* of the reps, it appears.
        if representative_ids:
            # Build a subquery for bills that any of these reps voted on
            votes_lateral = func.jsonb_array_elements(VoteEvent.votes).alias("vote_element")

            # Build the conditions for matching representative IDs
            or_conditions = []
            for rep_id in representative_ids:
                condition = json.dumps({"voter_id": rep_id})
                or_conditions.append(text(f"vote_element @> '{condition}'"))

            # Create the subquery that uses the LATERAL join to filter votes
            rep_vote_bill_ids = (
                select(VoteEvent.bill_id)
                .join(votes_lateral, text("true"))  # Perform LATERAL join
                .where(or_(*or_conditions))
                .distinct()
            )

            # Restrict bills to those that appear in the subquery
            bills_query = bills_query.where(BillTable.id.in_(rep_vote_bill_ids))

        # --- COUNT total for pagination ---
        total_bill_count = session.exec(
            select(func.count()).select_from(bills_query.subquery())
        ).one()
        log.info(f"Total bill count: {total_bill_count}")

        total_pages = ceil(total_bill_count / page_size)
        if page > total_pages and total_bill_count > 0:
            raise HTTPException(status_code=404, detail="Page not found.")

        # --- Sorting logic ---
        # We'll handle "latest_vote_date" with a subquery that calculates the MAX(VoteEvent.start_date).
        if sort_by == "latest_vote_date":
            sub_latest_vote = (
                select(
                    VoteEvent.bill_id,
                    func.max(VoteEvent.start_date).label("max_vote_date")
                )
                .group_by(VoteEvent.bill_id)
                .subquery()
            )
            # Outer join so bills with no votes won't be excluded
            # We then order by the subquery column "max_vote_date"
            bills_query = (
                bills_query
                .join(sub_latest_vote, BillTable.id == sub_latest_vote.c.bill_id, isouter=True)
            )

            if sort_order == "desc":
                bills_query = bills_query.order_by(desc(sub_latest_vote.c.max_vote_date))
            else:
                bills_query = bills_query.order_by(asc(sub_latest_vote.c.max_vote_date))

        else:
            # Simple column-based sorting
            if sort_by == "creation_date":
                sort_column = BillTable.created_at
            elif sort_by == "latest_action_date":
                sort_column = BillTable.latest_action_date
            elif sort_by == "title":
                sort_column = BillTable.title
            else:
                # default if an unknown sort_by is passed
                sort_column = BillTable.latest_action_date

            if sort_order == "desc":
                bills_query = bills_query.order_by(desc(sort_column))
            else:
                bills_query = bills_query.order_by(asc(sort_column))

        # --- Pagination ---
        bills_query = bills_query.offset((page - 1) * page_size).limit(page_size)
        bills = session.exec(bills_query).all()

        # Retrieve all votes for these bills
        bill_ids = [bill.id for bill in bills]
        votes = session.exec(
            select(VoteEvent).where(VoteEvent.bill_id.in_(bill_ids))
        ).all()

        # Attach votes
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

        # if not bill:
        #     raise HTTPException(status_code=404, detail="Bill not found")

        return bill_with_votes
    except Exception as e:
        log.exception(e)
        log.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Exception occurred when fetching bill.")