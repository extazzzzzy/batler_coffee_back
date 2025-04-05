from fastapi import FastAPI
from dotenv import load_dotenv
from app.router import create_router
import uvicorn
import asyncio
from app.dependencies import supabase
import multiprocessing
import os

load_dotenv()

app = FastAPI()

# Подключаем роутер
app.include_router(create_router(supabase))

@app.get("/")
async def health_check():
    return {"status": "ok", "services": ["fastapi", "telegram_bot"]}

def run_fastapi():
    uvicorn.run(app, host=os.getenv("DEPLOY_HOST"), port=int(os.getenv("DEPLOY_PORT")))

if __name__ == "__main__":
    # Создаем процессы для сервера
    fastapi_process = multiprocessing.Process(target=run_fastapi)
    fastapi_process.start()

    try:
        # Ожидаем завершения процессов (фактически будет работать бесконечно)
        fastapi_process.join()
    except KeyboardInterrupt:
        # Корректная обработка Ctrl+C
        print("\nОстановка сервера...")
        fastapi_process.terminate()
        fastapi_process.join()
        print("Сервер и бот остановлены")