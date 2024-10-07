from fastapi import APIRouter
from ..models import Representative

router = APIRouter()

@router.get("/representative/{representative_id}")
async def get_representative(representative_id: str):
    return {"representative_id": representative_id}

@router.get("/status/health")
async def get_status():
    return {"status": "running"}
