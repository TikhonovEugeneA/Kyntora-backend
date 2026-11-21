from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from uvicorn import run

from app.core.settings import get_settings
from app.ioc import AppProvider
from app.routers.router import router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="auth-service")
    app.include_router(router, prefix=settings.url_prefix.prefix)
    setup_dishka(make_async_container(AppProvider()), app)
    return app


app = create_app()

if __name__ == "__main__":
    fastapi_settings = get_settings().fastapi
    run(
        "app.main:app",
        reload=True,
        host=fastapi_settings.host,
        port=fastapi_settings.port,
    )
