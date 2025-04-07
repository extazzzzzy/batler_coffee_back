from fastapi import FastAPI
from dotenv import load_dotenv
from app.router import create_router
import uvicorn
from app.dependencies import supabase
import os

load_dotenv()

app = FastAPI()

# Подключаем роутер
app.include_router(create_router(supabase))

@app.get("/")
async def health_check():
    return {"status": "ok", "services": ["fastapi", "telegram_bot"]}

if __name__ == "__main__":
    uvicorn.run(app, host=os.getenv("DEPLOY_HOST"), port=int(os.getenv("DEPLOY_PORT")))