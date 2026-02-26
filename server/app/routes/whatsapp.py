from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.whatsapp import WhatsAppService, whatsapp_logs

router = APIRouter()

# Global instance to track state
current_wa_service = None

class WhatsAppRequest(BaseModel):
    message_template: str
    limit: int = 50 # Default safe limit

@router.post("/start")
def start_whatsapp(request: WhatsAppRequest):
    global current_wa_service, whatsapp_logs
    
    if current_wa_service and current_wa_service.is_running:
         raise HTTPException(status_code=400, detail="WhatsApp automation is already running.")
         
    whatsapp_logs.clear()
    
    current_wa_service = WhatsAppService(
        message_template=request.message_template,
        limit=request.limit
    )
    current_wa_service.start_in_background()
    
    return {"status": "started", "message": "WhatsApp automation started. Please check server logs/browser for QR code setup."}

@router.get("/status")
def get_whatsapp_status():
    return {
        "status": "running" if current_wa_service and current_wa_service.is_running else "idle",
        "logs": whatsapp_logs
    }
