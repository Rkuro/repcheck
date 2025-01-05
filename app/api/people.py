from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
import logging
import traceback

from ..database.database import get_session
from ..database.models import Area, Person, PersonTable, PersonWithAreas, PersonArea

router = APIRouter(prefix="/api")
log = logging.getLogger(__name__)

@router.get("/people/{zip_code}", response_model=List[PersonWithAreas])
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
        people = session.exec(
            select(PersonTable)
            .where(PersonTable.id.in_(person_ids))
        ).all()

        area_ids = set([])
        people_with_areas = []
        for p in people:
            people_with_areas.append(PersonWithAreas(**p.dict()))
            area_ids.add(p.constituent_area_id)
            area_ids.add(p.jurisdiction_area_id)

        areas = session.exec(
            select(Area)
            .where(Area.id.in_(area_ids))
        ).all()

        # Tag them onto the objects
        for p_with_area in people_with_areas:
            for area in areas:
                if p_with_area.constituent_area_id == area.id:
                    p_with_area.constituent_area = area.dict(exclude={"geometry"})
                if p_with_area.jurisdiction_area_id == area.id:
                    p_with_area.jurisdiction_area = area.dict(exclude={"geometry"})

        return people_with_areas
    except Exception:
        log.error(f"Exception occurred: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching representatives.",
        )


@router.post("/people", response_model=List[Person])
def get_representatives(ids: List[str], session: Session = Depends(get_session)):
    try:
        people = session.exec(select(PersonTable).where(PersonTable.id.in_(ids))).all()

        return people
    except Exception:
        log.error(f"Exception occurred: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching representatives.",
        )