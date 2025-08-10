from fastapi import APIRouter
from app.channels.webchat.webhook import router as webchat_router
router = APIRouter()
router.include_router(webchat_router, prefix="/webchat", tags=["webchat"])
