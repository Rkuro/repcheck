from fastapi import APIRouter
import logging

router = APIRouter(prefix="/api")
log = logging.getLogger(__name__)


@router.get("/status/health")
async def get_status():
    return {"status": "running"}
