from fastapi import APIRouter


router = APIRouter()


@router.get("/health")
async def admin_health_check() -> dict:
    return {"status": "ok", "scope": "admin"}

