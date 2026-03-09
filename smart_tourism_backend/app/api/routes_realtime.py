from fastapi import APIRouter


router = APIRouter()


@router.get("/health")
async def realtime_health_check() -> dict:
    return {"status": "ok", "scope": "realtime"}

