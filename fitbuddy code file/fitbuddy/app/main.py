"""
FitBuddy -- AI Fitness Plan Generator (Gemini 3.8 Flash)

Run with:
    uvicorn app.main:app --reload

Then visit:
    http://127.0.0.1:8000        the app
    http://127.0.0.1:8000/docs   interactive API docs
"""
from dotenv import load_dotenv

load_dotenv()  # loads GOOGLE_API_KEY from .env before anything else is imported

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.routes import router

app = FastAPI(title="FitBuddy -- AI Fitness Plan Generator")

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(router)


@app.on_event("startup")
def on_startup():
    init_db()
