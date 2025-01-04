from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
import logging
import traceback

from ..database.database import get_session
from ..database.models import Area, Person, PersonArea

router = APIRouter(prefix="/api")
log = logging.getLogger(__name__)

@router.get("/people/{zip_code}", response_model=List[Person])
def get_representatives_by_zip(zip_code: str, session: Session = Depends(get_session)):
    try:

        area_id = f"ocd-division/country:us/zipcode:{zip_code}"

        # Fetch person IDs for people associated with the zip code
        person_ids = (
            session.exec(
                select(PersonArea.person_id)
                .where(PersonArea.area_id == area_id)
                .distinct()
            )
            .all()
        )

        log.info(f"Found person IDs {person_ids} for zipcode {zip_code}")

        # Fetch Person records for those person_ids
        people = session.exec(select(Person).where(Person.id.in_(person_ids))).all()

        return people
    except Exception:
        log.error(f"Exception occurred: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching representatives.",
        )


@router.post("/people", response_model=List[Person])
def get_representatives(ids: List[str], session: Session = Depends(get_session)):
    try:
        people = session.exec(select(Person).where(Person.id.in_(ids))).all()

        return people
    except Exception:
        log.error(f"Exception occurred: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching representatives.",
        )