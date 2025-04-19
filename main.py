from fastapi import FastAPI
from dotenv import load_dotenv
from app.router import create_router
import uvicorn
from app.dependencies import supabase
import os
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()

# Подключаем роутер
app.include_router(create_router(supabase))

allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def health_check():
    return {"status": "ok", "services": ["fastapi", "telegram_bot"]}

if __name__ == "__main__":
    uvicorn.run(app, host=os.getenv("DEPLOY_HOST"), port=int(os.getenv("DEPLOY_PORT")))