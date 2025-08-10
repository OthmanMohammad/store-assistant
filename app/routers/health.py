from fastapi import APIRouter
router = APIRouter()
@router.get("/readyz")
def readyz(): return {"ok": True}
