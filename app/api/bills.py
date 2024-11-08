# from fastapi import APIRouter, Depends, HTTPException
# from sqlmodel import Session, select, text
# from typing import List
# import logging
# import traceback
# from math import ceil

# from ..database import get_db
# from ..database.models import Bill, ZipcodePeopleJoinTable, Person
# from pydantic import BaseModel

# router = APIRouter(prefix="/api")
# log = logging.getLogger(__name__)

# class PaginatedBills(BaseModel):
#     total_bills: int
#     total_pages: int
#     current_page: int
#     page_size: int
#     bills: List[Bill]

# @router.get("/zipcodes/{zip_code}/bills", response_model=PaginatedBills)
# def get_bills_for_representatives(
#     zip_code: str,
#     page: int = 1,
#     page_size: int = 20,
#     db: Session = Depends(get_db),
# ):
#     try:
#         # Validate page and page_size
#         if page < 1 or page_size < 1:
#             raise HTTPException(
#                 status_code=400, detail="page and page_size must be positive integers."
#             )

#         # Fetch person IDs associated with the zip code
#         person_ids = db.exec(
#             select(ZipcodePeopleJoinTable.person_id)
#             .where(ZipcodePeopleJoinTable.zip_code == zip_code)
#             .join(Person)
#         ).all()
#         person_ids = [pid[0] for pid in person_ids]

#         if not person_ids:
#             return PaginatedBills(
#                 total_bills=0,
#                 total_pages=0,
#                 current_page=page,
#                 page_size=page_size,
#                 bills=[],
#             )

#         # Count total bills for people
#         total_bills_for_persons = (
#             db.exec(Bill.id)
#             .filter(
#                 text("jsonb_path_exists(votes, '$[*].votes[*].voter.id ? (@ == $id)') = ANY(:person_ids)")
#             )
#             .params(person_ids=person_ids)
#             .distinct()
#             .count()
#         )

#         # Calculate total pages
#         total_pages = ceil(total_bills_for_persons / page_size)

#         if page > total_pages and total_bills_for_persons > 0:
#             raise HTTPException(status_code=404, detail="Page not found.")

#         # Query bills with pagination
#         bills = (
#             db.exec(
#                 select(Bill)
#                 .filter(
#                     text("jsonb_path_exists(votes, '$[*].votes[*].voter.id ? (@ == $id)') = ANY(:person_ids)")
#                 )
#                 .order_by(Bill.updated_at.desc())
#                 .distinct()
#                 .offset((page - 1) * page_size)
#                 .limit(page_size)
#                 .params(person_ids=person_ids)
#             ).all()
#         )

#         return PaginatedBills(
#             total_bills=total_bills_for_persons,
#             total_pages=total_pages,
#             current_page=page,
#             page_size=page_size,
#             bills=bills,
#         )
#     except Exception:
#         log.error(f"Exception occurred: {traceback.format_exc()}")
#         raise HTTPException(
#             status_code=500,
#             detail="An error occurred while fetching bills.",
#         )
