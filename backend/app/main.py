# ~/marketnews-app/backend/app/main.py
import os
import re
from typing import Generator, Any, Dict

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import JSONResponse

# import DB & models if you use them (keeps your existing endpoints working)
from . import db, models

# import routers
from .routers import market_summary, announcements

# -----------------------
# Path helpers (project layout)
# backend/
#   app/           <-- this file lives here
#   data/          <-- CSV files (eod_YYYY-MM-DD.csv)
#   static/images/ <-- logos
#   announcements/uploads/ <-- announcement images/PDFs
# -----------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
STATIC_IMAGES_DIR = os.path.join(PROJECT_ROOT, "static", "images")
ANNOUNCEMENTS_UPLOADS_DIR = os.path.join(PROJECT_ROOT, "announcements", "uploads")

# ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(STATIC_IMAGES_DIR, exist_ok=True)
os.makedirs(ANNOUNCEMENTS_UPLOADS_DIR, exist_ok=True)

app = FastAPI(title="MarketNews API", version="0.3")

# CORS - allow all during development (tighten later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# mount static folders
app.mount("/static/images", StaticFiles(directory=STATIC_IMAGES_DIR), name="static_images")
app.mount("/announcements/file", StaticFiles(directory=ANNOUNCEMENTS_UPLOADS_DIR), name="announcements_files")

# include routers
app.include_router(market_summary.router)
app.include_router(announcements.router)


# -----------------------
# DB session dependency
# -----------------------
def get_db() -> Generator:
    database = db.SessionLocal()
    try:
        yield database
    finally:
        database.close()


# -----------------------
# Root & health
# -----------------------
@app.get("/")
def read_root():
    return {"message": "MarketNews API is running 🚀"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


# -----------------------
# Card endpoints (from DB)
# -----------------------
@app.post("/cards")
def create_card(card: dict, database=Depends(get_db)):
    new_card = models.Card(**card)
    database.add(new_card)
    database.commit()
    database.refresh(new_card)
    return {"id": new_card.id, "message": "Card created"}


@app.get("/cards")
def list_cards(database=Depends(get_db)):
    cards = database.query(models.Card).all()
    return cards


# -----------------------
# Debug endpoint
# -----------------------
@app.get("/debug/static-status")
def debug_static_status():
    return {
        "static_images_dir": STATIC_IMAGES_DIR,
        "announcements_uploads_dir": ANNOUNCEMENTS_UPLOADS_DIR,
        "data_dir": DATA_DIR,
    }


# -----------------------
# Error handler
# -----------------------
@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)