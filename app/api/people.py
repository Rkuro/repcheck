from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
import logging
import traceback

from ..database.database import get_db
from ..database.models import Zipcode, ZipcodePeopleJoinTable, Person

router = APIRouter(prefix="/api")
log = logging.getLogger(__name__)

@router.get("/people/{zip_code}", response_model=List[Person])
def get_representatives(zip_code: str, db: Session = Depends(get_db)):
    try:
        # Fetch the ZIP code record
        zipcode = db.exec(select(Zipcode).where(Zipcode.zip_code == zip_code)).first()
        if zipcode is None:
            raise HTTPException(status_code=404, detail="ZIP code not found")

        # Get all person_ids associated with the ZIP code
        person_ids = db.exec(
            select(ZipcodePeopleJoinTable.person_id).where(ZipcodePeopleJoinTable.zip_code == zip_code)
        ).all()

        log.info(f"Found people {person_ids} for zipcode {zip_code}")
        if not person_ids:
            return []

        # Fetch Person records for those person_ids
        representatives = db.exec(select(Person).where(Person.id.in_(person_ids))).all()

        return representatives
    except Exception:
        log.error(f"Exception occurred: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching representatives.",
        )
