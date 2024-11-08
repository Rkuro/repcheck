from fastapi import APIRouter, Depends, HTTPException
import logging
import traceback
from sqlalchemy.orm import Session
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping
from ..database.database import get_db
from ..database.models import Zipcode

router = APIRouter(prefix="/api")
log = logging.getLogger(__name__)


@router.get("/status/health")
async def get_status():
    return {"status": "running"}
