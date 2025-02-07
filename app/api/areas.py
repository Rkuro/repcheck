from fastapi import APIRouter, Depends, HTTPException
import traceback
import logging
from sqlalchemy.sql import select, func
from sqlalchemy.orm import Session
from geoalchemy2.shape import to_shape
from geoalchemy2 import Geography
from shapely.geometry import mapping
from ..database.database import get_session
from ..database.models import Area, PrecinctElectionResultArea
from haversine import haversine, Unit
import math

router = APIRouter(prefix="/api")
log = logging.getLogger(__name__)

MILES_TO_METERS = 1609.34

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


@router.get("/precincts/{zip_code}")
def get_precincts_by_centroid(
        zip_code: str,
        radius_miles: float = 5.0,
        session: Session = Depends(get_session)
):
    """
    Return precincts whose centroid is within `radius_miles` miles
    of the ZIP code's centroid.
    """
    try:

        # Check for too big/small radius
        if 100 > radius_miles < 1:
            raise HTTPException(status_code=400, detail="Radius miles must be between 1 and 100")

        # 1) Get the ZIP area
        zip_code_area_id = f"ocd-division/country:us/zipcode:{zip_code}"
        area = session.execute(
            select(Area).where(Area.id == zip_code_area_id)
        ).scalar_one_or_none()

        if not area:
            raise HTTPException(status_code=404, detail="ZIP code not found")

        lat_zip = area.centroid_lat
        lon_zip = area.centroid_lon

        if lat_zip is None or lon_zip is None:
            raise HTTPException(status_code=400, detail="ZIP code centroid missing lat/lon")

        # 2) Approx bounding box (for better performance)
        deg_lat = radius_miles / 69.0
        # cos(latitude) in radians
        deg_lon = radius_miles / (69.0 * math.cos(math.radians(lat_zip)))

        lat_min = lat_zip - deg_lat
        lat_max = lat_zip + deg_lat
        lon_min = lon_zip - deg_lon
        lon_max = lon_zip + deg_lon

        # 3) Query precincts that are in the bounding box
        precincts_in_box = (
            session.query(PrecinctElectionResultArea)
            .filter(PrecinctElectionResultArea.centroid_lat.between(lat_min, lat_max))
            .filter(PrecinctElectionResultArea.centroid_lon.between(lon_min, lon_max))
            .all()
        )

        # 4) Filter by actual Haversine
        precincts_in_radius = []
        for p in precincts_in_box:
            dist = haversine(
                (lat_zip,lon_zip),
                (p.centroid_lat,p.centroid_lon),
                unit=Unit.MILES
            )
            if dist <= radius_miles:
                json_geo = mapping(to_shape(p.geometry))
                p_dict = p.model_dump()
                p_dict["geometry"] = json_geo
                precincts_in_radius.append(p_dict)

        # 5) Return some or all data
        return {
            "zip_code": zip_code,
            "radius_miles": radius_miles,
            "count": len(precincts_in_radius),
            "precincts": precincts_in_radius,
        }
    except HTTPException:
        raise
    except Exception as e:
        log.exception("Error retrieving precincts")
        return {
            "error": str(e),
            "zip_code": zip_code,
            "precincts": []
        }