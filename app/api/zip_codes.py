from fastapi import APIRouter, Depends, HTTPException
import traceback
import logging
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
        zipcode = session.query(Area).where(Area.classification ==
                                       'zipcode' and Area.abbrev == zip_code).first()
    
        if zipcode is None:
            raise HTTPException(status_code=404, detail="ZIP code not found")
        
        geom = to_shape(zipcode.geometry)
        
        # Return the ZIP code along with geometry in GeoJSON format
        return {
            "zip_code": zipcode.zip_code,
            "geometry": mapping(geom),  # Convert geometry to GeoJSON,
            "error": None
        }
    except:
        log.error(f"Exception occurred: {traceback.format_exc()}")
        return {
            "zip_code": None,
            "geometry": None,
            "error": "Exception occurred fetching zipcode from database. Check logs"
        }