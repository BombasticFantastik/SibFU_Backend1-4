import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


from config import settings
from contextlib import asynccontextmanager
from fastapi_pagination import add_pagination
from models import db_helper, Base
from api import router as api_router
from task_queue.taskiq_broker import broker 

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Код при СТАРТЕ приложения ---
    print("🚀 Подключаем Taskiq брокер...")
    if not broker.is_worker_process:
        await broker.startup()
    print("✅ Брокер готов к работе!")
    
    yield  # Здесь приложение "работает"
    
    # --- Код при ВЫКЛЮЧЕНИИ приложения ---
    print("🛑 Отключаем брокер...")
    if not broker.is_worker_process:
        await broker.shutdown()
    print("👋 Брокер отключен.")


main_app = FastAPI(
    lifespan=lifespan,
)

main_app.include_router(
    api_router,
)

main_app.mount("/static", StaticFiles(directory="static"), name="static")
add_pagination(main_app)

if __name__ == "__main__":
    uvicorn.run(
        "main:main_app",
        host=settings.run.host,
        port=settings.run.port,
        reload=settings.run.reload,
    )

