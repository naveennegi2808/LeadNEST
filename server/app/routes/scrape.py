from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from typing import List

from app.services.scraper import GMBScraper, scrape_logs
from app.services import scraper as scraper_module

router = APIRouter()

class ScrapeRequest(BaseModel):
    keywords: str
    relevanceKeywords: str
    city: str
    country: str
    limit: int

def run_scraper_task(request: ScrapeRequest):
    scraper = GMBScraper(
        keywords_str=request.keywords,
        relevance_keywords_str=request.relevanceKeywords,
        city=request.city,
        country=request.country,
        limit=request.limit
    )
    scraper_module.current_scraper = scraper
    scraper.run()
    scraper_module.current_scraper = None

@router.post("/start")
def start_scraping(request: ScrapeRequest, background_tasks: BackgroundTasks):
    scraper_module.scrape_logs.clear()
    
    background_tasks.add_task(run_scraper_task, request)
    return {"status": "started", "message": "Scraping process initiated in the background."}

@router.post("/stop")
def stop_scraping():
    if scraper_module.current_scraper:
        scraper_module.current_scraper.should_stop = True
        return {"status": "stopping", "message": "Stop signal sent to scraper."}
    return {"status": "idle", "message": "No active scraper running."}

@router.get("/status")
def get_scrape_status():
    # In a full production app, Websockets or Server-Sent Events (SSE) are better.
    # For this MVP, we use simple polling to fetch logs.
    current_logs = scraper_module.scrape_logs
    return {
        "status": "running" if current_logs and "Done!" not in current_logs[-1] else "idle",
        "logs": current_logs
    }
