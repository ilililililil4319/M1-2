from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(title="네이버 재무건전성 AI 비서 API")

allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routers import data, conversations, chat
app.include_router(data.router)
app.include_router(conversations.router)
app.include_router(chat.router)

@app.get("/")
def root():
    return {"status": "ok", "message": "네이버 재무건전성 AI 비서 API"}
