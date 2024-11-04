from fastapi import APIRouter, Depends, HTTPException
import logging
import traceback
from sqlalchemy.orm import Session
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping
from ..database.database import get_db
from ..models import ZipCode

router = APIRouter(prefix="/api")
log = logging.getLogger(__name__)

# Endpoint to fetch a specific ZIP code by zip_code
@router.get("/zipcodes/{zip_code}")
def read_zipcode(zip_code: str, db: Session = Depends(get_db)):
    try:
        zipcode = db.query(ZipCode).filter(ZipCode.zip_code == zip_code).first()
    
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

@router.get("/status/health")
async def get_status():
    return {"status": "running"}
