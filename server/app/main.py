from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import scrape, whatsapp, auth

app = FastAPI(title="GMB Scraper & WhatsApp Automation API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(scrape.router, prefix="/api/scrape", tags=["Scraping"])
app.include_router(whatsapp.router, prefix="/api/whatsapp", tags=["WhatsApp"])

@app.get("/")
def read_root():
    return {"message": "Welcome to GMB Scraper & WhatsApp Automation API"}
