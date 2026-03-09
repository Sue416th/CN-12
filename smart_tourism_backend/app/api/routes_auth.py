from fastapi import APIRouter


router = APIRouter()


@router.get("/health")
async def auth_health_check() -> dict:
    return {"status": "ok", "scope": "auth"}

