from fastapi import APIRouter, Depends, HTTPException
import traceback
import logging
from sqlalchemy.sql import select
from sqlalchemy.orm import Session
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping
from ..database.database import get_session
from ..database.models import Area

router = APIRouter(prefix="/api")
log = logging.getLogger(__name__)

# Endpoint to fetch a specific ZIP code by zip_code
@router.get("/zipcodes/{zip_code}")
def read_zipcode(zip_code: str, session: Session = Depends(get_session)):
    try:

        zip_code_area_id = f"ocd-division/country:us/zipcode:{zip_code}"
        area = session.execute(
            select(Area)
            .where(Area.id == zip_code_area_id)
        ).scalars().one()
    
        if not area:
            raise HTTPException(status_code=404, detail="ZIP code not found")
        # log.info(f"Zip code: {area}")
        geom = to_shape(area.geometry)
        
        # Return the ZIP code along with geometry in GeoJSON format
        return {
            "zip_code": zip_code,
            "area": area.dict(exclude={"geometry"}),
            "geometry": mapping(geom),  # Convert geometry to GeoJSON
            "error": None
        }
    except:
        log.error(f"Exception occurred: {traceback.format_exc()}")
        return {
            "zip_code": None,
            "geometry": None,
            "error": "Exception occurred fetching zipcode from database. Check logs"
        }


@router.get("/areas/{area_id:path}")
def read_zipcode(area_id: str, session: Session = Depends(get_session)):
    log.info(f"Area id: {area_id}")
    try:

        area = session.execute(
            select(Area.id, Area.geometry)
            .where(Area.id == area_id)
        ).one()

        if not area:
            raise HTTPException(status_code=404, detail="Area not found")
        log.info(f"Area: {area}")
        geom = to_shape(area.geometry)

        # Return the area id along with geometry in GeoJSON format
        return {
            "area_id": area_id,
            "geometry": mapping(geom),  # Convert geometry to GeoJSON
            "error": None
        }
    except:
        log.error(f"Exception occurred: {traceback.format_exc()}")
        return {
            "area_id": None,
            "geometry": None,
            "error": "Exception occurred fetching area from database. Check logs"
        }