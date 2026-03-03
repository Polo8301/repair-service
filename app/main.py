from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from .routers import requests
from .database import engine, Base

# Создаём таблицы при старте
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Ремонтная служба")

# 🔥 ВАЖНО: Создаём шаблоны И добавляем их в app
templates = Jinja2Templates(directory="app/templates")
app.templates = templates  # ← Эта строка была пропущена!

# Подключаем роутеры
app.include_router(requests.router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/test")
async def test_endpoint():
    """Простой эндпоинт для проверки"""
    return {"message": "Server is working!"}