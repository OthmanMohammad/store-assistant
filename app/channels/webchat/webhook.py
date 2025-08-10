from fastapi import APIRouter
from pydantic import BaseModel
router = APIRouter()

class WebMsg(BaseModel):
    text: str
    session_id: str | None = None
    locale: str | None = None

@router.post("/message")
async def message(msg: WebMsg):
    return {"session_id": msg.session_id or "local", "text": f"Echo: {msg.text}"}
