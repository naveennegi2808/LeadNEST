from fastapi import APIRouter
from pydantic import BaseModel
from app.services.google_sheets import sheets_service

router = APIRouter()

class AuthURLRequest(BaseModel):
    pass

@router.get("/url")
def get_auth_url():
    url = sheets_service.get_auth_url()
    return {"url": url}

@router.get("/status")
def get_auth_status():
    return {"authenticated": sheets_service.is_authenticated()}

@router.get("/status/leads")
def get_lead_count():
    return {"count": sheets_service.get_lead_count()}

from fastapi.responses import RedirectResponse
import urllib.parse

@router.get("/callback")
def auth_callback(code: str, state: str = None, scope: str = None):
    try:
        success = sheets_service.handle_callback(code)
        # Redirect back to the frontend sheets page on success
        return RedirectResponse(url="http://localhost:3001/sheets?status=success")
    except Exception as e:
        error_msg = urllib.parse.quote(str(e))
        return RedirectResponse(url=f"http://localhost:3001/sheets?status=error&message={error_msg}")

